import typing as t

from over_provisioning.logger import get_logger
from over_provisioning.pods_finder import OverProvisioningPodsFinder, Pod
from over_provisioning.tests.pods_spawner import PodsSpawner, PodCreationTimeHitsLimitError

logger = get_logger()


class OverProvisioningPodsStateChecker:
    def __init__(self, over_provisioning_pods_finder: OverProvisioningPodsFinder):
        self._over_provisioning_pods_finder = over_provisioning_pods_finder

        self._initial_pods: t.List[Pod] = None

    def set_initial_pods(self):
        self._initial_pods = self._over_provisioning_pods_finder.find_pods()

    def is_all_pods_recreated_on_new_nodes(self) -> bool:
        current_pods = self._over_provisioning_pods_finder.find_pods()

        if not self._all_pods_was_recreated(current_pods):
            return False
        if not self._all_old_was_pods_removed(current_pods):
            return False
        if not self._is_old_nodes_used(current_pods):
            return False
        return True

    def _all_pods_was_recreated(self, current_pods: t.List[Pod]) -> bool:
        return len(current_pods) == len(self._initial_pods)

    def _is_old_nodes_used(self, current_pods: t.List[Pod]) -> bool:
        initial_nodes = [pod.node_name for pod in self._initial_pods]
        current_nodes = [pod.node_name for pod in current_pods]
        old_nodes = set(initial_nodes).intersection(set(current_nodes))
        return len(old_nodes) == 0

    def _all_old_was_pods_removed(self, current_pods: t.List[Pod]) -> bool:
        initial_pods_names = [pod.name for pod in self._initial_pods]
        current_pods_names = [pod.name for pod in current_pods]
        old_pods_names = set(initial_pods_names).intersection(set(current_pods_names))
        return len(old_pods_names) == 0

    def last_pod_was_removed(self) -> bool:
        current_pods = self._over_provisioning_pods_finder.find_pods()
        return self._all_old_was_pods_removed(current_pods)


class PodCreatingLoop:
    """For one over provisioning pod"""

    def __init__(
            self,
            pods_spawner: PodsSpawner,
            # over_provisioning_pods_finder: OverProvisioningPodsFinder,
            over_provisioning_pods_state_checker: OverProvisioningPodsStateChecker,
            pods_to_create_quantity: int = None,
    ):
        self._pods_spawner = pods_spawner
        # self._over_provisioning_pods_finder = over_provisioning_pods_finder
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

            if self._over_provisioning_state_checker.last_pod_was_removed():
                last_pod_created_without_delay = self._create_next_pod("extra", max_pod_creation_time_in_seconds)

                if last_pod_created_without_delay:
                    # todo wait until all OPPs will have assigned nodes
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
