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

    def _check_nodes_assigned(self, pods_to_check: t.Iterable[str]) -> t.Iterable[Pod]:
        for pod_name in pods_to_check:
            is_node_assigned, node_name = self._node_was_assigned(pod_name)
            if is_node_assigned:
                yield Pod(pod_name, node_name)

    def _updated_pods_with_unassigned_nodes(self, pods_with_assigned_nodes: t.Iterable[Pod]):
        for pod in pods_with_assigned_nodes:
            logger.info(f"New node: {pod.node_name}  assigned for pod: {pod.name}")
            self._pods_with_unassigned_nodes.remove(pod.name)

    def wait_on_pods(self, pods_names: t.Iterable[str]):
        self._pods_with_unassigned_nodes = set(pods_names)

        with Timer() as timer:
            while self._pods_with_unassigned_nodes.copy():
                logger.info(
                    f"Waiting on assigning nodes for the following pods: {str(self._pods_with_unassigned_nodes)}."
                    f" Waited time: {timer.elapsed} seconds"
                )
                pods_with_assigned_nodes = self._check_nodes_assigned(self._pods_with_unassigned_nodes)
                self._updated_pods_with_unassigned_nodes(pods_with_assigned_nodes)

                if self._is_time_limit_exhausted(timer.elapsed):
                    return False

                self._wait(self._wait_interval)

        logger.info(f"All over provisioning pods was assigned to new nodes. Waited time: {timer.elapsed} seconds")
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
