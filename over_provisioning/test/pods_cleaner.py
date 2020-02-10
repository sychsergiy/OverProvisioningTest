import typing as t

from over_provisioning.kuber.pod_deleter import PodDeleter
from over_provisioning.logger import get_logger

logger = get_logger()


class PodsCleaner:
    def __init__(self, pod_deleter: PodDeleter):
        self._pod_deleter = pod_deleter
        self._pods_to_delete: t.List[str] = []

    def set_pods_to_delete(self, pods_to_delete: t.List[str]):
        self._pods_to_delete = pods_to_delete

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clean()
        if exc_type is not None:
            return False  # reraise exception

    def clean(self) -> bool:
        try:
            logger.info(f"Trying to cleanup the following pods: {str(self._pods_to_delete)}")
            self._pod_deleter.delete_many(self._pods_to_delete)
            logger.info(f"Successfully cleanup pods: {str(self._pods_to_delete)}")
            return True
        except Exception:
            logger.exception("Failed to cleanup pods due to the following exception")
            logger.info("Manual pods cleanup required")
            return False
