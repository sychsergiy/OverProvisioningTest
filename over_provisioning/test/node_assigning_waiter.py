import typing as t
import time

from over_provisioning.kuber.pod_reader import PodReader
from over_provisioning.logger import get_logger
from over_provisioning.pods_finder import Pod
from over_provisioning.timer import Timer

logger = get_logger()


class NodesAssigningWaiter:
    def __init__(self, pod_reader: PodReader, max_waiting_time: float, wait_interval: float = 60):
        self._pod_reader = pod_reader
        self._max_waiting_time = max_waiting_time
        self._wait_interval = wait_interval

        self._pods_with_unassigned_nodes: t.Set[str] = set()

    def _all_pods_has_assigned_nodes(self) -> bool:
        return len(self._pods_with_unassigned_nodes) == 0

    def wait_on_pods(self, pods_names: t.List[str]):
        self._pods_with_unassigned_nodes = set(pods_names)

        with Timer() as timer:
            while not self._all_pods_has_assigned_nodes():
                pods_to_check = self._pods_with_unassigned_nodes.copy()
                logger.info(
                    f"Waiting on assigning nodes for the following pods: {str(pods_to_check)}."
                    f" Waited time: {timer.elapsed}"
                )

                for pod_name in pods_to_check:
                    is_assigned, node_name = self._node_was_assigned(pod_name)
                    if is_assigned:
                        self._pods_with_unassigned_nodes.remove(pod_name)
                        logger.info(f"New node: {node_name}  assigned for pod: {pod_name}")

                if self._is_time_limit_exhausted(timer.elapsed):
                    return False

                self._wait(self._wait_interval)

        logger.info(f"All over provisioning pods was assigned to new nodes. Waited time: {timer.elapsed}")
        return True

    @staticmethod
    def _wait(time_to_wait: float):
        time.sleep(time_to_wait)

    def _is_time_limit_exhausted(self, waited_time: float) -> bool:
        return waited_time > self._max_waiting_time

    def _get_assigned_node_name(self, pod_name: str) -> t.Optional[str]:
        pod = self._pod_reader.read(pod_name)
        return pod.spec.node_name

    def _node_was_assigned(self, pod_name) -> t.Tuple[bool, str]:
        assigned_node = self._get_assigned_node_name(pod_name)

        is_node_assigned = assigned_node is not None
        if is_node_assigned:
            return True, assigned_node
        return False, ""
