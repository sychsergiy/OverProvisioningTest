from over_provisioning.logger import get_logger
from over_provisioning.tests.pods_spawner import PodsSpawner, PodCreationTimeHitsLimitError
from over_provisioning.tests.pods_state_checker import OverProvisioningPodsStateChecker

logger = get_logger()


class PodCreatingLoop:
    """For one over provisioning pod"""

    def __init__(
            self,
            pods_spawner: PodsSpawner,
            over_provisioning_pods_state_checker: OverProvisioningPodsStateChecker,
            pods_to_create_quantity: int = None,
    ):
        self._pods_spawner = pods_spawner
        self._over_provisioning_state_checker = over_provisioning_pods_state_checker

        self._pods_to_create_quantity = pods_to_create_quantity

    def get_created_pods(self):
        return self._pods_spawner.get_created_pods()

    def _create_next_pod(
            self, pod_sequence_number: int, max_pod_creation_time_in_seconds: float
    ) -> float:
        try:
            self._pods_spawner.create_pod(pod_sequence_number, max_pod_creation_time_in_seconds)
        except PodCreationTimeHitsLimitError:
            logger.exception("Pod creation failed")
            return False
        return True

    def run(self, max_pod_creation_time_in_seconds: float):
        self._over_provisioning_state_checker.set_initial_pods()

        i = 1
        while True:
            ok = self._create_next_pod(i, max_pod_creation_time_in_seconds)
            if not ok:
                return False

            newly_created_pods = self._over_provisioning_state_checker.get_newly_created_pods()
            if newly_created_pods:
                logger.info(f"The following over provisioning pods was created: {str(newly_created_pods)}")

            if self._over_provisioning_state_checker.last_pod_was_removed():
                last_pod_created_without_delay = self._create_next_pod("extra", max_pod_creation_time_in_seconds)

                if last_pod_created_without_delay:
                    # todo: measure time of nodes creation

                    if not self._over_provisioning_state_checker.wait_on_nodes_assigning():
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
