import time
import typing as t

from over_provisioning.kuber.pod_reader import PodReader
from over_provisioning.logger import get_logger
from over_provisioning.pods_finder import OverProvisioningPodsFinder, Pod
from over_provisioning.tests.pods_spawner import PodsSpawner, PodCreationTimeHitsLimitError
from over_provisioning.timer import Timer

logger = get_logger()


class NodesAssigningWaiter:
    def __init__(self, pod_reader: PodReader, max_waiting_time: float, wait_interval: float = 0.5):
        self._pod_reader = pod_reader
        self._max_waiting_time = max_waiting_time
        self._wait_interval = wait_interval

        self._pods_to_check: t.Set[str] = set()

    def wait_on_pods(self, pods_names: t.List[str]):
        self._pods_to_check = set(pods_names)

        with Timer() as timer:
            while self._pods_to_check:
                pods_to_check = self._pods_to_check.copy()
                logger.info(
                    f"Waiting on assigning nodes for the following pods: {str(pods_to_check)}."
                    f" Waited time: {timer.elapsed}"
                )

                for pod_name in pods_to_check:
                    assigned_node = self._get_assigned_node(pod_name)
                    if assigned_node:
                        self._pods_to_check.remove(pod_name)
                        logger.info(f"New node: {assigned_node}  assigned for pod: {pod_name}")

                if timer.elapsed > self._max_waiting_time:
                    return False
                time.sleep(self._wait_interval)

        logger.info(f"All over provisioning pods was assigned to new nodes. Waited time: {timer.elapsed}")
        return True

    def _get_assigned_node(self, pod_name: str) -> t.Optional[str]:
        pod = self._pod_reader.read(pod_name)
        return pod.spec.node_name


class OverProvisioningPodsStateChecker:
    def __init__(
            self, over_provisioning_pods_finder: OverProvisioningPodsFinder,
            node_assigning_waiter: NodesAssigningWaiter
    ):
        self._over_provisioning_pods_finder = over_provisioning_pods_finder
        self._node_assigning_waiter = node_assigning_waiter

        self._initial_pods: t.List[Pod] = []
        self._created_pods: t.Set[str] = set()

    @property
    def created_pods(self) -> t.Set[str]:
        return self._created_pods

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

    def get_newly_created_pods(self) -> t.Set[str]:
        initial_pods_names = [pod.name for pod in self._initial_pods]
        current_pods = self._over_provisioning_pods_finder.find_pods()
        current_pods_names = [pod.name for pod in current_pods]

        recreated_pods = set(current_pods_names) - set(initial_pods_names)

        newly_created_pods = self._created_pods - recreated_pods
        if newly_created_pods:
            self._created_pods = self._created_pods.union(newly_created_pods)
        return newly_created_pods

    def wait_on_nodes_assigning(self) -> bool:
        current_pods_names = self._over_provisioning_pods_finder.find_pods()
        pods_names_with_unassigned_nodes = [pod.name for pod in current_pods_names if pod.node_name is None]
        return self._node_assigning_waiter.wait_on_pods(pods_names_with_unassigned_nodes)


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
