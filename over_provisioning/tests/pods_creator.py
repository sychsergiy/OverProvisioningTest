import logging

from over_provisioning.kuber.pod_creator import PodCreator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PodCreationTimeHitsLimitError(Exception):
    def __init__(self, pod_name: str, creation_time_limit: float):
        self.pod_name = pod_name
        self.creation_time_limit = creation_time_limit

    def __str__(self):
        return f"Pod creating: {self.pod_name} time hit the limit: {self.creation_time_limit}."


class PodsCreator:
    def __init__(self, pod_creator: PodCreator, pods_base_name: str):
        self._pod_creator = pod_creator
        self._pods_base_name = pods_base_name

        self._created_pods_names = []

    def _construct_pod_name(self, pod_sequence_number: int):
        return f"{self._pods_base_name}-{pod_sequence_number}"

    def get_created_pods(self):
        return self._created_pods_names

    def create_pod(self, pod_sequence_number: int, max_pod_creation_time: float) -> float:
        """
        returns time waited until pod ready and created pod_name
        """
        pod_name = self._construct_pod_name(pod_sequence_number)

        logger.info(f"Init pod creation. Pod name: {pod_name}")
        _, pod_creation_time = self._pod_creator.create_pod(pod_name)
        logger.info(f"Pod creation time: {pod_creation_time}")

        logger.info(f"Wait until pod is ready")
        ok, pod_getting_ready_time = self._pod_creator.wait_until_pod_ready(pod_name, max_pod_creation_time)
        if not ok:
            raise PodCreationTimeHitsLimitError(pod_name, max_pod_creation_time)
        logger.info(f"Waited time: {pod_getting_ready_time}\n")

        self._created_pods_names.append(pod_name)

        return pod_creation_time + pod_getting_ready_time
