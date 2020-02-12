import typing as t

from over_provisioning.environment.setuper import EnvironmentSetuper
from over_provisioning.kuber.nodes_finder import NodesFinder
from over_provisioning.logger import get_logger
from over_provisioning.test.pod_creating_loop import PodCreatingLoop
from over_provisioning.test.pods_cleaner import PodsCleaner
from over_provisioning.test.report_builder import ReportBuilder

logger = get_logger()


class OneOverProvisioningPodTest:
    def __init__(
        self,
        pod_creating_loop: PodCreatingLoop,
        nodes_finder: NodesFinder,
        environment_setuper: EnvironmentSetuper,
        pod_cleaner: PodsCleaner,
        report_builder: ReportBuilder,
    ):
        self._pod_creating_loop = pod_creating_loop
        self._nodes_finder = nodes_finder
        self._environment_setuper = environment_setuper
        self._pods_cleaner = pod_cleaner
        self._report_builder = report_builder

    def run(
        self, max_pod_creation_time_in_seconds: float
    ) -> t.Tuple[bool, dict]:
        with self._environment_setuper as env_created_successfully:
            if env_created_successfully:
                with self._pods_cleaner as pods_cleaner:
                    initial_amount_of_nodes = len(
                        self._nodes_finder.find_by_label_selector()
                    )
                    logger.info(
                        f"Initial amount of nodes: {initial_amount_of_nodes}"
                    )

                    test_result = self._pod_creating_loop.run(
                        max_pod_creation_time_in_seconds
                    )
                    pods_cleaner.set_pods_to_delete(
                        self._pod_creating_loop.get_created_pods()
                    )

                    amount_of_nodes_after_test = len(
                        self._nodes_finder.find_by_label_selector()
                    )
                    logger.info(
                        f"Amount of nodes after the test: {amount_of_nodes_after_test}"
                    )

                    self._report_builder.set_nodes_report(
                        initial_amount_of_nodes, amount_of_nodes_after_test
                    )

                    return test_result, self._report_builder.build_report()
        return False, self._report_builder.build_report()
