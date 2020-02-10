import time

from over_provisioning.kuber.pod_reader import PodReader
from over_provisioning.logger import get_logger
from over_provisioning.timer import Timer

logger = get_logger()


class PodWaiter:
    def __init__(self, pod_reader: PodReader):
        self._pod_reader = pod_reader

    def wait_until_pod_ready(self, pod_name: str, max_waiting_time: float, read_pod_interval: float = 0.5) -> bool:
        with Timer() as timer:
            while True:
                pod = self._pod_reader.read(pod_name)
                if self.is_pod_ready(pod):
                    return True
                else:
                    time.sleep(read_pod_interval)
                    if timer.elapsed > max_waiting_time:
                        return False

    @staticmethod
    def is_pod_ready(pod) -> bool:
        if not pod.status.conditions:
            return False
        statuses = [item.type for item in pod.status.conditions]
        return "Ready" in statuses

    @staticmethod
    def has_pod_running_status(pod) -> bool:
        return pod.status.phase == "Running"

    def wait_on_running_status(self, pod_name: str, max_waiting_time: float, read_pod_interval: float = 0.5) -> bool:
        with Timer() as timer:
            logger.info(f"Wait until pod status is \"Running\", start time: {timer.start_time}")
            while True:
                pod = self._pod_reader.read(pod_name)
                if self.has_pod_running_status(pod):
                    logger.info(f"Waited time: {timer.elapsed}\n")
                    return True
                else:
                    time.sleep(read_pod_interval)
                    spent_time = timer.elapsed
                    if spent_time > max_waiting_time:
                        return False
