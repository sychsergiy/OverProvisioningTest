from over_provisioning.logger import get_logger
from over_provisioning.test.node_assigning_waiter import NodesAssigningWaiter
from over_provisioning.test.nodes_assigning_timeout_handler import NodesAssigningTimeoutHandler
from over_provisioning.test.pods_spawner import PodsSpawner, PodCreationTimeHitsLimitError
from over_provisioning.test.op_pods_state import OverProvisioningPodsState
from over_provisioning.test.report_builder import ReportBuilder

logger = get_logger()


class PodCreatingLoop:
    """For one over provisioning pod"""

    def __init__(
            self,
            pods_spawner: PodsSpawner,
            over_provisioning_pods_state: OverProvisioningPodsState,
            nodes_assigning_waiter: NodesAssigningWaiter,
            node_assigning_timeout_handler: NodesAssigningTimeoutHandler,
            report_builder: ReportBuilder,
            pods_to_create_quantity: int = None,
    ):
        self._pods_spawner = pods_spawner
        self._over_provisioning_pods_state = over_provisioning_pods_state
        self._node_assigning_waiter = nodes_assigning_waiter
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
            self._report_builder.add_error(f"Pod creation timeout error")
            return False
        return True

    def _create_extra_pod(self, max_pod_creation_time_in_seconds: float) -> bool:
        try:
            pod_name, creation_time = self._pods_spawner.create_pod("extra", max_pod_creation_time_in_seconds)
            self._report_builder.set_extra_pod_creation_time(creation_time)
        except PodCreationTimeHitsLimitError:
            self._report_builder.add_error("Extra pod creation timout error")
            logger.exception("Pod creation failed")
            return False
        return True

    def run(self, max_pod_creation_time_in_seconds: float):
        self._over_provisioning_pods_state.set_initial_pods()

        i = 1
        while True:
            ok = self._create_next_pod(str(i), max_pod_creation_time_in_seconds)
            if not ok:
                return False

            newly_created_pods = self._over_provisioning_pods_state.save_newly_created_pods()
            if newly_created_pods:
                logger.info(f"The following over provisioning pods was created: {str(newly_created_pods)}")

            if self._over_provisioning_pods_state.last_pod_was_removed():
                last_pod_created_without_delay = self._create_extra_pod(max_pod_creation_time_in_seconds)
                self._report_builder.set_op_pods_time_creation_map(
                    self._over_provisioning_pods_state.pods_creation_time_map
                )
                if last_pod_created_without_delay:
                    pods_to_wait_on = self._over_provisioning_pods_state.created_pods

                    self._node_assigning_waiter.set_pods_to_wait_on(pods_to_wait_on)
                    if not self._node_assigning_waiter.wait():
                        self._report_builder.set_op_pods_nodes_assigning_time_map(
                            self._node_assigning_waiter.pods_node_assigning_time_map
                        )
                        self._node_assigning_timeout_handler.handle()
                        return False
                    self._report_builder.set_op_pods_nodes_assigning_time_map(
                        self._node_assigning_waiter.pods_node_assigning_time_map
                    )

                    if self._over_provisioning_pods_state.is_all_pods_recreated_on_new_nodes():
                        return True
                    return False
                return False

            if self._is_created_pods_quantity_hits_limit(i):
                message = f"Hit the limit of pods quantity: {self._pods_to_create_quantity}"
                self._report_builder.add_error(message)
                logger.info(message)
                return False

            i += 1

    def _is_created_pods_quantity_hits_limit(self, pods_quantity: int):
        if self._pods_to_create_quantity is None:
            # pods_to_create_quantity None value means infinite pod creation
            # always return False
            return False
        return pods_quantity >= self._pods_to_create_quantity
