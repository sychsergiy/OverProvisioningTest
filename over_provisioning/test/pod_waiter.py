import time
import typing as t

from over_provisioning.kuber.pod_reader import PodReader
from over_provisioning.logger import get_logger
from over_provisioning.timer import Timer

logger = get_logger()


class PodWaiter:
    def __init__(self, pod_reader: PodReader, read_pod_interval: float):
        self._pod_reader = pod_reader
        self._read_pod_interval = read_pod_interval

    @staticmethod
    def _is_status_running(pod_status) -> bool:
        return pod_status == "Running"

    def _read_pod_status(self, pod_name: str) -> str:
        pod = self._pod_reader.read(pod_name)
        return pod.status.phase

    @staticmethod
    def _is_time_limit_exhausted(
        waited_time: float, max_waiting_time: float
    ) -> bool:
        return waited_time > max_waiting_time

    def wait_on_running_status(
        self, pod_name: str, max_waiting_time: float
    ) -> t.Tuple[bool, float]:
        with Timer() as timer:
            logger.info(
                f'Wait until pod status is "Running", start time: {timer.start_time}'
            )
            while True:
                if self._has_pod_running_status(pod_name):
                    logger.info(f"Waited time: {timer.elapsed}\n")
                    return True, timer.elapsed
                else:
                    if self._is_time_limit_exhausted(
                        timer.elapsed, max_waiting_time
                    ):
                        return False, timer.elapsed
                    else:
                        self._wait(self._read_pod_interval)

    def _has_pod_running_status(self, pod_name: str) -> bool:
        pod_status = self._read_pod_status(pod_name)
        return self._is_status_running(pod_status)

    @staticmethod
    def _wait(time_in_seconds: float):
        time.sleep(time_in_seconds)
