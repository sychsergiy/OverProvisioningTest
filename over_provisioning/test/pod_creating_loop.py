from over_provisioning.logger import get_logger
from over_provisioning.test.nodes_assigning_timeout_handler import NodesAssigningTimeoutHandler
from over_provisioning.test.pods_spawner import PodsSpawner, PodCreationTimeHitsLimitError
from over_provisioning.test.pods_state_checker import OverProvisioningPodsStateChecker
from over_provisioning.test.report_builder import ReportBuilder

logger = get_logger()


class PodCreatingLoop:
    """For one over provisioning pod"""

    def __init__(
            self,
            pods_spawner: PodsSpawner,
            over_provisioning_pods_state_checker: OverProvisioningPodsStateChecker,
            node_assigning_timeout_handler: NodesAssigningTimeoutHandler,
            report_builder: ReportBuilder,
            pods_to_create_quantity: int = None,
    ):
        self._pods_spawner = pods_spawner
        self._over_provisioning_state_checker = over_provisioning_pods_state_checker
        self._node_assigning_timeout_handler = node_assigning_timeout_handler

        self._pods_to_create_quantity = pods_to_create_quantity
        self._report_builder = report_builder

    def get_created_pods(self):
        return self._pods_spawner.get_created_pods()

    def _create_next_pod(
            self, pod_name_suffix: str, max_pod_creation_time_in_seconds: float
    ) -> bool:
        try:
            pod_name, creation_time = self._pods_spawner.create_pod(pod_name_suffix, max_pod_creation_time_in_seconds)
            self._report_builder.add_pod_creation_report(pod_name, creation_time)
        except PodCreationTimeHitsLimitError:
            logger.exception("Pod creation failed")
            return False
        return True

    def _create_extra_pod(self, max_pod_creation_time_in_seconds: float) -> bool:
        try:
            pod_name, creation_time = self._pods_spawner.create_pod("extra", max_pod_creation_time_in_seconds)
            self._report_builder.set_extra_pod_creation_time(creation_time)
        except PodCreationTimeHitsLimitError:
            logger.exception("Pod creation failed")
            return False
        return True

    def run(self, max_pod_creation_time_in_seconds: float):
        self._over_provisioning_state_checker.set_initial_pods()

        i = 1
        while True:
            ok = self._create_next_pod(str(i), max_pod_creation_time_in_seconds)
            if not ok:
                return False

            newly_created_pods = self._over_provisioning_state_checker.get_newly_created_pods()
            if newly_created_pods:
                logger.info(f"The following over provisioning pods was created: {str(newly_created_pods)}")

            if self._over_provisioning_state_checker.last_pod_was_removed():
                last_pod_created_without_delay = self._create_extra_pod(max_pod_creation_time_in_seconds)

                if last_pod_created_without_delay:
                    # todo: measure time of nodes creation

                    if not self._over_provisioning_state_checker.wait_on_nodes_assigning():
                        self._node_assigning_timeout_handler.handle()
                        logger.info("Finish the test because of the limit on waiting for node assigning")
                        return False
                    if self._over_provisioning_state_checker.is_all_pods_recreated_on_new_nodes():
                        return True
                    return False
                return False

            if self._is_created_pods_quantity_hits_limit(i):
                logger.info(
                    "Finish the test because of hit the limit of pods quantity"
                )
                return False

            i += 1

    def _is_created_pods_quantity_hits_limit(self, pods_quantity: int):
        if self._pods_to_create_quantity is None:
            # pods_to_create_quantity None value means infinite pod creation
            # always return False
            return False
        return pods_quantity >= self._pods_to_create_quantity
