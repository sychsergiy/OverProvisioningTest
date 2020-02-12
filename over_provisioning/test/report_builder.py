import typing as t


class NodeAssigning(t.NamedTuple):
    node_name: str
    timestamp: float


class PodCreationReport(t.NamedTuple):
    pod_name: str
    creation_time: float


class OverProvisioningPodReport(t.NamedTuple):
    pod_name: str
    assigned_node: str
    node_assigning_time: float


class NodesReport(t.NamedTuple):
    quantity_before_start: int
    quantity_after_end: int


class ReportBuilder:
    def __init__(self):
        self._pod_creation_reports: t.List[PodCreationReport] = []
        self._nodes_report: t.Optional[NodesReport] = None
        self._extra_pod_creation_time: float = 0

        self._op_pods_time_creation_map: t.Dict[str, float] = {}
        self._op_pods_node_assigning_map: t.Dict[str, NodeAssigning] = dict()

        self._errors: t.List[str] = []

    def add_error(self, error_message: str):
        self._errors.append(error_message)

    def add_pod_creation_report(self, pod_name: str, creation_time: float):
        self._pod_creation_reports.append(PodCreationReport(pod_name, creation_time))

    def set_op_pods_time_creation_map(self, time_creation_map: t.Dict[str, float]):
        self._op_pods_time_creation_map = time_creation_map

    def set_op_pods_nodes_assigning_time_map(self, node_assigning_time_map: t.Dict[str, NodeAssigning]):
        self._op_pods_node_assigning_map = node_assigning_time_map

    def set_nodes_report(self, quantity_before_start: int, quantity_after_end: int):
        self._nodes_report = NodesReport(quantity_before_start, quantity_after_end)

    def set_extra_pod_creation_time(self, value: float):
        self._extra_pod_creation_time = value

    def _calc_average_pod_creation_time(self) -> float:
        quantity = len(self._pod_creation_reports)
        if quantity == 0:
            return 0
        total_sum = sum([report.creation_time for report in self._pod_creation_reports])
        return total_sum / quantity

    def build_report(self) -> dict:
        return {
            "nodes_before_start": self._nodes_report.quantity_before_start,
            "nodes_after_end": self._nodes_report.quantity_after_end,
            "amount_of_created_pods": len(self._pod_creation_reports),
            "average_pod_creation_time": self._calc_average_pod_creation_time(),
            "extra_pod_creation_time": self._extra_pod_creation_time,
            "over_provisioning": {
                "creation_time_map": self._op_pods_time_creation_map,
                "node_assigning_map": {
                    pod: node_assigning._asdict() for pod, node_assigning in self._op_pods_node_assigning_map.items()
                },
            },
            "errors": self._errors,
        }
