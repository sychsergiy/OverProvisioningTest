import typing as t
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
        pods_nodes_before = self._find_over_provisioning_pods()

        logger.info(f"Init pod creation. Pod name: {pod_name}")
        _, execution_time = self._pod_creator.create_pod(pod_name)
        logger.info(f"Pod creation time: {execution_time}")

        if execution_time > max_pod_creation_time_in_seconds:
            return self.IterationResult.POD_CREATION_TIME_HIT_THE_LIMIT

        logger.info(f"Wait until pod is ready")
        _, waited_time = self._pod_creator.wait_until_pod_ready(pod_name)
        logger.info(f"Waited time: {waited_time}\n")

        self._created_pods_names.append(pod_name)

        pods_nodes_after = self._find_over_provisioning_pods()

        if pods_nodes_after != pods_nodes_before:

            # check if there are pods with not assigned pods
            for pod_name, node_name in pods_nodes_after.keys():
                if node_name is None:
                    # if yes: wait on node assigning
                    self._over_provisioning_pods_finder.wait_until_node_assigned(pod_name)
                    pods_nodes_after = self._find_over_provisioning_pods()

            # check only one over provisioning was recreated
            if self._does_one_over_provisioning_was_recreated_on_new_node(pods_nodes_before, pods_nodes_after):
                # if yes: continue
                return self.IterationResult.OVER_PROVISIONING_POD_CHANGED_NODE
            else:
                # else: raise exception
                raise RuntimeError(
                    f"Unexpected behaviour. "
                    f"More than one over provisioning pod was recreated on new node per iteration "
                    f"or pod was recreated on the same node\n"
                    f"Over provisioning pods before pod creation: \n{str(pods_nodes_before)}\n"
                    f"Over provisioning pods after pod creation: \n{str(pods_nodes_after)}\n"
                )

    @staticmethod
    def _does_one_over_provisioning_was_recreated_on_new_node(
        pods_nodes_before: t.Dict[str, str], pods_nodes_after: t.Dict[str, str]
    ) -> bool:
        # check one pod created
        created_pod_names = list(set(pods_nodes_after.keys()) - set(pods_nodes_before.keys()))
        if len(created_pod_names) != 1:
            return False

        # check one pod removed
        removed_pod_names = list(set(pods_nodes_before.keys()) - set(pods_nodes_after.keys()))
        if len(removed_pod_names) != 1:
            return False

        # check pod created on new node
        new_pod_name, removed_pod_name = created_pod_names[0], removed_pod_names[0]
        node_assigned_to_new_pod = pods_nodes_after[new_pod_name]
        node_assigned_to_old_pod = pods_nodes_before[removed_pod_name]
        if node_assigned_to_new_pod == node_assigned_to_old_pod:
            return False

        return True

    def _find_over_provisioning_pods(self) -> t.Dict[str, str]:
        pods = self._over_provisioning_pods_finder.find_pods()
        return {pod.name: pod.node_name for pod in pods}

    @staticmethod
    def _does_all_old_over_provisioning_pods_removed(
        initial_pods_nodes: t.Dict[str, str], current_pods_nodes: t.Dict[str, str]
    ) -> bool:
        not_recreated_pods_names = set(initial_pods_nodes.keys()).intersection(set(current_pods_nodes.keys()))
        all_old_pods_removed = len(not_recreated_pods_names) == 0
        return all_old_pods_removed

    def run(self, max_pod_creation_time_in_seconds):
        i = 1

        initial_over_prov_pods_nodes_map = self._find_over_provisioning_pods()

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
                # check all over provisioning pod was recreated on new nodes
                # if yes finish test (result test is passed)
                pods_nodes = self._find_over_provisioning_pods()
                if self._does_all_old_over_provisioning_pods_removed(initial_over_prov_pods_nodes_map, pods_nodes):
                    return True

            if self._pods_to_create_quantity:
                if i >= self._pods_to_create_quantity:
                    logger.info(
                        "Finish the test because of hit the limit of pods quantity"
                    )
                    return False
            i += 1
