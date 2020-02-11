import kubernetes
import typing as t

from over_provisioning.kuber.pod_creator import PodCreator
from over_provisioning.logger import get_logger
from over_provisioning.test.pod_waiter import PodWaiter
from over_provisioning.test.report_builder import ReportBuilder

logger = get_logger()


class PodCreationTimeHitsLimitError(Exception):
    def __init__(self, pod_name: str, creation_time_limit: float):
        self.pod_name = pod_name
        self.creation_time_limit = creation_time_limit

    def __str__(self):
        return f"Pod creating: {self.pod_name} time hit the limit: {self.creation_time_limit}."


class PodsSpawner:
    def __init__(
            self, pod_creator: PodCreator,  pod_waiter: PodWaiter, pods_base_name: str,
            pod_spec: kubernetes.client.V1PodSpec
    ):
        self._pod_creator = pod_creator
        self._pod_waiter = pod_waiter
        self._pods_base_name = pods_base_name
        self._pod_spec = pod_spec

        self._created_pods_names = []

    def _construct_pod_name(self, pod_name_suffix: str):
        return f"{self._pods_base_name}-{pod_name_suffix}"

    def get_created_pods(self):
        return self._created_pods_names

    def create_pod(self, pod_name_suffix: str, max_pod_creation_time: float) -> t.Tuple[str, float]:
        """
        returns time waited until pod ready and created pod_name
        """
        pod_name = self._construct_pod_name(pod_name_suffix)

        logger.info(f"Init pod creation. Pod name: {pod_name}")
        pod_creation_time = self._pod_creator.create_pod(pod_name, self._pod_spec)
        logger.info(f"Pod creation time: {pod_creation_time}")

        self._created_pods_names.append(pod_name)

        time_limit_not_hited, waited_time = self._pod_waiter.wait_on_running_status(
            pod_name, max_pod_creation_time - pod_creation_time
        )
        if not time_limit_not_hited:
            raise PodCreationTimeHitsLimitError(pod_name, max_pod_creation_time)

        return pod_name, pod_creation_time + waited_time
