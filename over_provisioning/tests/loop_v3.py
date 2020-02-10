from over_provisioning.kuber.nodes_finder import NodesFinder
from over_provisioning.logger import get_logger
from over_provisioning.pods_finder import OverProvisioningPodsFinder, Pod
from over_provisioning.tests.pods_spawner import PodsSpawner, PodCreationTimeHitsLimitError

logger = get_logger()


class PodCreatingLoop:
    """For one over provisioning pod"""

    def __init__(
            self,
            pods_spawner: PodsSpawner,
            over_provisioning_pods_finder: OverProvisioningPodsFinder,
            nodes_finder: NodesFinder,
            pods_to_create_quantity: int = None,
    ):
        self._pods_spawner = pods_spawner
        self._over_provisioning_pods_finder = over_provisioning_pods_finder
        self._nodes_finder = nodes_finder

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
        i = 1

        initial_over_prov_pods = self._over_provisioning_pods_finder.find_pods()

        while True:
            ok = self._create_next_pod(i, max_pod_creation_time_in_seconds)
            if not ok:
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
