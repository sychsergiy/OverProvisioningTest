import typing as t

from over_provisioning.pods_finder import OverProvisioningPodsFinder, Pod
from over_provisioning.test.node_assigning_waiter import NodesAssigningWaiter


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

        newly_created_pods = recreated_pods - self._created_pods
        if newly_created_pods:
            self._created_pods = self._created_pods.union(newly_created_pods)
        return newly_created_pods

    def wait_on_nodes_assigning(self) -> bool:
        current_pods_names = self._over_provisioning_pods_finder.find_pods()
        pods_names_with_unassigned_nodes = [pod.name for pod in current_pods_names if pod.node_name is None]
        return self._node_assigning_waiter.wait_on_pods(pods_names_with_unassigned_nodes)
