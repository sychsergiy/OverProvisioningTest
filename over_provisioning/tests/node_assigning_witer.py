import typing as t
import time

from over_provisioning.kuber.pod_reader import PodReader
from over_provisioning.logger import get_logger
from over_provisioning.timer import Timer

logger = get_logger()


class NodesAssigningWaiter:
    def __init__(self, pod_reader: PodReader, max_waiting_time: float, wait_interval: float = 60):
        self._pod_reader = pod_reader
        self._max_waiting_time = max_waiting_time
        self._wait_interval = wait_interval

        self._pods_to_check: t.Set[str] = set()

    def wait_on_pods(self, pods_names: t.List[str]):
        self._pods_to_check = set(pods_names)

        with Timer() as timer:
            while self._pods_to_check:
                pods_to_check = self._pods_to_check.copy()
                logger.info(
                    f"Waiting on assigning nodes for the following pods: {str(pods_to_check)}."
                    f" Waited time: {timer.elapsed} seconds"
                )

                for pod_name in pods_to_check:
                    assigned_node = self._get_assigned_node(pod_name)
                    if assigned_node:
                        self._pods_to_check.remove(pod_name)
                        logger.info(f"New node: {assigned_node}  assigned for pod: {pod_name}")

                if timer.elapsed > self._max_waiting_time:
                    return False
                time.sleep(self._wait_interval)

        logger.info(f"All over provisioning pods was assigned to new nodes. Waited time: {timer.elapsed} seconds")
        return True

    def _get_assigned_node(self, pod_name: str) -> t.Optional[str]:
        pod = self._pod_reader.read(pod_name)
        return pod.spec.node_name
