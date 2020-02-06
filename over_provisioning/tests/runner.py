import logging

from over_provisioning.environment_setuper import EnvironmentSetuper
from over_provisioning.nodes_finder import NodesFinder
from over_provisioning.pod_creator import PodDeleter
from over_provisioning.tests.pod_creating_loop import PodCreatingLoop

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OneOverProvisioningPodTest:
    """
    Current version of test will work's only when one over provisioning pod is present in namespace.
    """

    def __init__(
            self, pod_creating_loop: PodCreatingLoop,
            nodes_finder: NodesFinder,
            environment_setuper: EnvironmentSetuper,
            pod_deleter: PodDeleter,
    ):
        self._pod_creating_loop = pod_creating_loop
        self._nodes_finder = nodes_finder
        self._environment_setuper = environment_setuper
        self._pod_deleter = pod_deleter

    def _pre_run(self):
        self._environment_setuper.create()

        initial_amount_of_nodes = len(self._nodes_finder.find_by_label_selector())
        logger.info(f"Initial amount of nodes: {initial_amount_of_nodes}")

    def _post_run(self):
        amount_of_nodes_after_test = len(self._nodes_finder.find_by_label_selector())
        logger.info(f"Amount of nodes after the test: {amount_of_nodes_after_test}")

        self._cleanup_environment()

    def _delete_created_pods(self):
        pods_to_delete = self._pod_creating_loop.get_created_pods()
        try:
            self._pod_deleter.delete_many(pods_to_delete)
        except Exception:
            logger.critical("Failed to cleanup created pods. Manual cleanup required")

    def _cleanup_environment(self):
        self._delete_created_pods()
        try:
            self._environment_setuper.destroy()
        except Exception:
            logger.critical("Failed to destroy environment. Manual cleanup required")

    def run(self, max_pod_creation_time_in_seconds: float) -> bool:
        self._pre_run()

        try:
            test_result = self._pod_creating_loop.run(max_pod_creation_time_in_seconds)
        except Exception as e:
            self._cleanup_environment()
            raise e

        self._post_run()

        return test_result
