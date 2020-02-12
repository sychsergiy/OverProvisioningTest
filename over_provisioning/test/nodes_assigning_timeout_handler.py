from over_provisioning.kuber.nodes_finder import NodesFinder
from over_provisioning.logger import get_logger
from over_provisioning.test.report_builder import ReportBuilder

logger = get_logger()


class NodesAssigningTimeoutHandler:
    def __init__(self, report_builder: ReportBuilder, nodes_finder: NodesFinder, max_available_nodes_to_create: int):
        self._report_builder = report_builder
        self._nodes_finder = nodes_finder
        self._max_available_nodes_to_create = max_available_nodes_to_create

    def _get_amount_of_nodes(self):
        return len(self._nodes_finder.find_by_label_selector())

    def handle(self):
        message = "Over provisioning pods nodes assigning timeout error"
        logger.warning(message)
        self._report_builder.add_error(message)
        amount_of_created_nodes = self._get_amount_of_nodes()

        if amount_of_created_nodes >= self._max_available_nodes_to_create:
            message = f"Max amount of created nodes: {self._max_available_nodes_to_create} reached"
            logger.warning(message)
            self._report_builder.add_error(message)
            self._send_alarm()

    def _send_alarm(self):
        # todo: implement sending alarm somewhere
        pass


def test_nodes_assigning_timeout_handler_handle():
    report_builder = ReportBuilder()
    nodes_finder = NodesFinder(None, "test_selector")
    nodes_finder.find_by_label_selector = lambda: ["node_1", "node_2"]

    handler = NodesAssigningTimeoutHandler(report_builder, nodes_finder, 3)
    handler.handle()

    assert report_builder._errors == ["Over provisioning pods nodes assigning timeout error"]


def test_nodes_assigning_timeout_handler_handle_max_amount_of_nodes_reached():
    report_builder = ReportBuilder()
    nodes_finder = NodesFinder(None, "test_selector")
    nodes_finder.find_by_label_selector = lambda: ["node_1", "node_2"]

    handler = NodesAssigningTimeoutHandler(report_builder, nodes_finder, 2)
    handler.handle()

    assert report_builder._errors == [
        "Over provisioning pods nodes assigning timeout error",
        "Max amount of created nodes: 2 reached",
    ]
