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
        self._nodes_report: t.Optional[NodesReport] = NodesReport(None, None)
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

    def _construct_over_provisioning(self) -> dict:
        result = dict()

        for pod_name, time_creation in self._op_pods_time_creation_map.items():
            result[pod_name] = {
                "creation_time": time_creation
            }
            node_assigning = self._op_pods_node_assigning_map.get(pod_name)
            if node_assigning:
                time_to_create = node_assigning.timestamp - time_creation
                result[pod_name].update({
                    "node_assigning_time": node_assigning.timestamp,
                    "time_to_assign_node": time_to_create,
                    "assigned_node": node_assigning.node_name
                })
        return result

    def build_report(self) -> dict:
        return {
            "nodes_before_start": self._nodes_report.quantity_before_start,
            "nodes_after_end": self._nodes_report.quantity_after_end,
            "amount_of_created_pods": len(self._pod_creation_reports),
            "average_pod_creation_time": self._calc_average_pod_creation_time(),
            "extra_pod_creation_time": self._extra_pod_creation_time,
            "over_provisioning_pods": self._construct_over_provisioning(),
            "errors": self._errors,
        }


def test_build_report():
    report_builder = ReportBuilder()
    report_builder.set_op_pods_time_creation_map(
        {"test1": 100, "test2": 100}
    )
    report_builder.set_op_pods_nodes_assigning_time_map(
        {"test1": NodeAssigning("test_node1", 150), "test2": NodeAssigning("test_node2", 150)}
    )
    result = report_builder.build_report()

    expected_result = {
        "nodes_before_start": None,
        "nodes_after_end": None,
        "amount_of_created_pods": 0,
        "average_pod_creation_time": 0,
        "extra_pod_creation_time": 0,
        "over_provisioning_pods": {
            "test1": {"creation_time": 100, "assigned_node": "test_node1", "time_to_assign_node": 50,
                      "node_assigning_time": 150},
            "test2": {"creation_time": 100, "assigned_node": "test_node2", "time_to_assign_node": 50,
                      "node_assigning_time": 150},
        },
        "errors": [],
    }
    assert expected_result == result
