import enum
import logging

from over_provisioning.kuber.nodes_finder import NodesFinder
from over_provisioning.pods_finder import OverProvisioningPodsFinder, Pod
from over_provisioning.tests.pods_creator import PodsCreator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PodCreatingLoop:
    """For one over provisioning pod"""

    class IterationResult(enum.Enum):
        POD_CREATION_TIME_HIT_THE_LIMIT = "POD_CREATION_TIME_HIT_THE_LIMIT"
        OVER_PROVISIONING_POD_CHANGED_NODE = "OVER_PROVISIONING_POD_CHANGED_NODE"

    def __init__(
            self,
            pods_creator: PodsCreator,
            over_provisioning_pods_finder: OverProvisioningPodsFinder,
            nodes_finder: NodesFinder,
            pods_to_create_quantity: int = None,
    ):
        self._pods_creator = pods_creator
        self._over_provisioning_pods_finder = over_provisioning_pods_finder
        self._nodes_finder = nodes_finder

        self._pods_to_create_quantity = pods_to_create_quantity

    def get_created_pods(self):
        return self._pods_creator.get_created_pods()

    def _next_creating_pod_iteration(
            self, pod_sequence_number: int, max_pod_creation_time_in_seconds: float
    ):
        over_provisioning_pod = self._find_over_provisioning_pod()

        waited_time = self._pods_creator.create_pod(pod_sequence_number, max_pod_creation_time_in_seconds)

        if waited_time > max_pod_creation_time_in_seconds:
            return self.IterationResult.POD_CREATION_TIME_HIT_THE_LIMIT

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
        result = pod.name != over_provisioning_pod.name and pod.node_name != over_provisioning_pod.node_name

        if result:
            logger.info(f"Old pod name: {pod.name}, old node: {pod.node_name}")
            logger.info(f"Created pod name: {over_provisioning_pod.name}, assigned node: {over_provisioning_pod.node_name}")
        return result

    def run(self, max_pod_creation_time_in_seconds):
        i = 1
        while True:
            iteration_result = self._next_creating_pod_iteration(
                i, max_pod_creation_time_in_seconds
            )
            if iteration_result == self.IterationResult.POD_CREATION_TIME_HIT_THE_LIMIT:
                logger.info(f"Pod creation time hit the limit: {max_pod_creation_time_in_seconds}.")
                return False

            if iteration_result == self.IterationResult.OVER_PROVISIONING_POD_CHANGED_NODE:
                logger.info(f"Over provisioning pod successfully changed node.")

                logger.info(f"Create extra pod")
                waited_time = self._pods_creator.create_pod(100, max_pod_creation_time_in_seconds)
                logger.info(f"Extra pod creation time: {waited_time}")
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
