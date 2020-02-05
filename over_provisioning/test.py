import time
import enum
import logging

from kubernetes import client, config

from over_provisioning.kuber_namespace import KuberNamespace
from over_provisioning.nodes_finder import NodesFinder
from over_provisioning.pod_creator import PodCreator
from over_provisioning.pods_finder import OverProvisioningPodsFinder, Pod

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_kuber(config_file_path=None):
    config.load_kube_config(config_file_path)
    kuber = client.CoreV1Api()
    return kuber


class OverProvisioningTest:
    class IterationResult(enum.Enum):
        POD_CREATION_TIME_HIT_THE_LIMIT = 1
        OVER_PROVISIONING_POD_CHANGED_NODE = 3

    """
    Current version of test will work's only when one over provisioning pod is present in namespace.
    """

    def __init__(
            self,
            pod_creator: PodCreator,
            over_provisioning_pods_finder: OverProvisioningPodsFinder,
            nodes_finder: NodesFinder,
            pods_to_create_quantity: int = None,
    ):
        self._pod_creator = pod_creator
        self._over_provisioning_pods_finder = over_provisioning_pods_finder
        self._nodes_finder = nodes_finder

        # will be not used if None
        self._pods_to_create_quantity = pods_to_create_quantity

    def _find_over_provisioning_pod(self) -> Pod:
        pods_map = self._over_provisioning_pods_finder.find_pods()
        pods_quantity = len(pods_map)

        if pods_quantity == 0:
            raise RuntimeError(f"Unexpected behaviour. Over provisioning pod not found.")
        if pods_quantity > 1:
            raise RuntimeError(f"Unexpected behaviour. One over provisioning pod expected, found: {pods_quantity}")

        return pods_map[0]

    def _does_over_provisioning_pod_changed_name_and_node(self, pod: Pod) -> bool:
        """
        Except of reassigning node, pod name will be also changed
        Because to move pod to another node Kubernetes
          it creates new pod(with new name and unassigned node) and deleting the old one,
          then waiting on new node creation
          then assign's newly created node to newly created pod
        """
        over_provisioning_pod = self._find_over_provisioning_pod()
        return pod.name != over_provisioning_pod.name and pod.node_name != over_provisioning_pod.node_name

    def _next_creating_pod_iteration(
            self, pod_name: str, max_pod_creation_time_in_seconds: float
    ):
        over_provisioning_pod = self._find_over_provisioning_pod()

        logger.info(f"Init pod creation. Pod name: {pod_name}")
        _, execution_time = self._pod_creator.create_pod(pod_name)
        logger.info(f"Pod creation time: {execution_time}")

        if execution_time > max_pod_creation_time_in_seconds:
            return self.IterationResult.POD_CREATION_TIME_HIT_THE_LIMIT

        logger.info(f"Wait until pod is ready")
        _, waited_time = self._pod_creator.wait_until_pod_ready(pod_name)
        logger.info(f"Waited time: {waited_time}\n")

        if self._does_over_provisioning_pod_changed_name_and_node(over_provisioning_pod):
            return self.IterationResult.OVER_PROVISIONING_POD_CHANGED_NODE

    @staticmethod
    def _construct_pod_name(pod_sequence_number: int):
        return f"test-pod-{pod_sequence_number}"

    def _run_creating_pod_loop(self, max_pod_creation_time_in_seconds: float):
        i = 1
        while True:
            pod_name_to_create = self._construct_pod_name(i)

            iteration_result = self._next_creating_pod_iteration(pod_name_to_create, max_pod_creation_time_in_seconds)
            if iteration_result == self.IterationResult.POD_CREATION_TIME_HIT_THE_LIMIT:
                logger.info(f"Pod creation time hit the limit: {max_pod_creation_time_in_seconds}.")
                return False

            if iteration_result == self.IterationResult.OVER_PROVISIONING_POD_CHANGED_NODE:
                logger.info(f"Over provisioning pod successfully changed node.")
                return True

            if self._pods_to_create_quantity:
                if i >= self._pods_to_create_quantity:
                    logger.info(
                        "Finish the test because of hit the limit of pods quantity"
                    )
                    return False

            i += 1

    def run(self, max_pod_creation_time_in_seconds) -> bool:
        initial_amount_of_nodes = len(self._nodes_finder.find_by_label_selector())
        logger.info(f"Initial amount of nodes: {initial_amount_of_nodes}")

        test_result = self._run_creating_pod_loop(max_pod_creation_time_in_seconds)

        amount_of_nodes_after_test = len(self._nodes_finder.find_by_label_selector())
        logger.info(f"Amount of nodes after the test: {amount_of_nodes_after_test}")
        return test_result


def run_test(
        kuber_namespace: KuberNamespace,
        create_new_namespace: bool,
        over_provisioning_test: OverProvisioningTest,
        max_pod_creation_time_in_seconds: float,
):
    if create_new_namespace:
        kuber_namespace.create()
        time.sleep(2)
    else:
        kuber_namespace.check_if_exists()

    result = over_provisioning_test.run(max_pod_creation_time_in_seconds)
    if result:
        logger.info("Test pass ......................")
    else:
        logger.info("Test failed ....................")

    if create_new_namespace:
        kuber_namespace.delete()
