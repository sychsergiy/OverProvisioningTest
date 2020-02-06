import enum
import logging

from over_provisioning.nodes_finder import NodesFinder
from over_provisioning.pod_creator import PodCreator
from over_provisioning.pods_finder import OverProvisioningPodsFinder, Pod

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PodCreatingLoop:
    """For one over provisioning pod"""

    class IterationResult(enum.Enum):
        POD_CREATION_TIME_HIT_THE_LIMIT = "POD_CREATION_TIME_HIT_THE_LIMIT"
        OVER_PROVISIONING_POD_CHANGED_NODE = "OVER_PROVISIONING_POD_CHANGED_NODE"

    def __init__(
            self,
            pod_creator: PodCreator,
            over_provisioning_pods_finder: OverProvisioningPodsFinder,
            nodes_finder: NodesFinder,
            pods_to_create_quantity: int = None,
    ):
        self._pod_creator = pod_creator
        self._over_provisioning_pods_finder = over_provisioning_pods_finder
        self._nodes_finder = nodes_finder

        self._pods_to_create_quantity = pods_to_create_quantity

        self._created_pods_names = []

    def get_created_pods(self):
        return self._created_pods_names

    @staticmethod
    def _construct_pod_name(pod_sequence_number: int):
        return f"test-pod-{pod_sequence_number}"

    def _next_creating_pod_iteration(
            self, pod_name: str, max_pod_creation_time_in_seconds: float
    ):
        over_provisioning_pod = self._find_over_provisioning_pod()

        logger.info(f"Init pod creation. Pod name: {pod_name}")
        _, execution_time = self._pod_creator.create_pod(pod_name)
        logger.info(f"Pod creation time: {execution_time}")

        if execution_time > max_pod_creation_time_in_seconds:
            return self.IterationResult.POD_CREATION_TIME_HIT_THE_LIMIT

        logger.info(f"Wait until pod is ready")
        _, waited_time = self._pod_creator.wait_until_pod_ready(pod_name)
        logger.info(f"Waited time: {waited_time}\n")

        self._created_pods_names.append(pod_name)

        if self._does_over_provisioning_pod_changed_name_and_node(over_provisioning_pod):
            return self.IterationResult.OVER_PROVISIONING_POD_CHANGED_NODE

    def _does_over_provisioning_pod_changed_name_and_node(self, pod: Pod) -> bool:
        """
        Except of reassigning node, pod name will be also changed
        Because to move pod to another node Kubernetes
          it creates new pod(with new name and unassigned node) and deleting the old one,
          then waiting on new node creation
          then assign's newly created node to newly created pod
        """
        over_provisioning_pod = self._find_over_provisioning_pod()
        return pod.name != over_provisioning_pod.name and pod.node_name != over_provisioning_pod.node_name

    def run(self, max_pod_creation_time_in_seconds):
        i = 1
        while True:
            pod_name_to_create = self._construct_pod_name(i)

            iteration_result = self._next_creating_pod_iteration(
                pod_name_to_create, max_pod_creation_time_in_seconds
            )
            if iteration_result == self.IterationResult.POD_CREATION_TIME_HIT_THE_LIMIT:
                logger.info(f"Pod creation time hit the limit: {max_pod_creation_time_in_seconds}.")
                return False

            if iteration_result == self.IterationResult.OVER_PROVISIONING_POD_CHANGED_NODE:
                logger.info(f"Over provisioning pod successfully changed node.")
                return True

            if self._pods_to_create_quantity:
                if i >= self._pods_to_create_quantity:
                    logger.info(
                        "Finish the test because of hit the limit of pods quantity"
                    )
                    return False

            i += 1

    def _find_over_provisioning_pod(self) -> Pod:
        pods = self._over_provisioning_pods_finder.find_pods()
        pods_quantity = len(pods)

        if pods_quantity == 0:
            raise RuntimeError(f"Unexpected behaviour. Over provisioning pod not found.")
        elif pods_quantity == 1:
            return pods[0]
        elif pods_quantity == 2:
            # check node one of the pods with unassigned pods
            logger.info(f"Pods: {str(pods)}")
            first_pod, second_pod = pods
            if first_pod.node_name is None:
                self._over_provisioning_pods_finder.wait_until_node_assigned(first_pod.name)
                return self._find_over_provisioning_pod()

            elif second_pod.node_name is None:
                self._over_provisioning_pods_finder.wait_until_node_assigned(second_pod.name)
                return self._find_over_provisioning_pod()
            else:
                raise RuntimeError(
                    f"Unexpected behaviour. Only two over provisioning pods can be present at the same time."
                    f"The first one the second with unassigned node. Found two with assigned nodes"
                )
        else:
            raise RuntimeError(f"Unexpected behaviour. One over provisioning pod expected, found: {pods_quantity}")