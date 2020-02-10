from over_provisioning.environment.setuper import EnvironmentSetuper
from over_provisioning.kuber.pod_deleter import PodDeleter
from over_provisioning.kuber.nodes_finder import NodesFinder
from over_provisioning.logger import get_logger
from over_provisioning.test.pod_creating_loop import PodCreatingLoop
from over_provisioning.test.pods_cleaner import PodsCleaner

logger = get_logger()


class OneOverProvisioningPodTest:
    """
    Current version of test will work's only when one over provisioning pod is present in namespace.
    """

    def __init__(
            self, pod_creating_loop: PodCreatingLoop,
            nodes_finder: NodesFinder,
            environment_setuper: EnvironmentSetuper,
            pod_cleaner: PodsCleaner
    ):
        self._pod_creating_loop = pod_creating_loop
        self._nodes_finder = nodes_finder
        self._environment_setuper = environment_setuper
        self._pods_cleaner = pod_cleaner

    def _pre_run(self):
        self._environment_setuper.create()

        initial_amount_of_nodes = len(self._nodes_finder.find_by_label_selector())
        logger.info(f"Initial amount of nodes: {initial_amount_of_nodes}")

    def _post_run(self):
        amount_of_nodes_after_test = len(self._nodes_finder.find_by_label_selector())
        logger.info(f"Amount of nodes after the test: {amount_of_nodes_after_test}")

        self._cleanup_environment()

    def _cleanup_environment(self):
        try:
            self._environment_setuper.destroy()
        except Exception:
            logger.critical("Failed to destroy environment. Manual cleanup required")

    def run(self, max_pod_creation_time_in_seconds: float) -> bool:
        self._pre_run()

        with self._pods_cleaner as pods_cleaner:
            test_result = self._pod_creating_loop.run(max_pod_creation_time_in_seconds)
            pods_cleaner.set_pods_to_delete(self._pod_creating_loop.get_created_pods())

        self._post_run()

        return test_result
