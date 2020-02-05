import time
import logging

from kubernetes import client, config

from over_provisioning.kuber_namespace import KuberNamespace
from over_provisioning.nodes_finder import NodesFinder
from over_provisioning.pod_creator import PodCreator
from over_provisioning.pods_finder import OverProvisioningPodsFinder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_kuber(config_file_path=None):
    config.load_kube_config(config_file_path)
    kuber = client.CoreV1Api()
    return kuber


class OverProvisioningTest:
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

    def _create_pod_and_until_ready(
            self, pod_name: str, max_pod_creation_time_in_seconds: float
    ) -> bool:
        logger.info(f"Init pod creation. Pod name: {pod_name}")
        _, execution_time = self._pod_creator.create_pod(pod_name)
        logger.info(f"Pod creation time: {execution_time}")

        if execution_time > max_pod_creation_time_in_seconds:
            logger.info("Pod creation time hit the limit. Test Failed")
            return False

        logger.info(f"Wait until pod is ready")
        _, waited_time = self._pod_creator.wait_until_pod_ready(pod_name)
        logger.info(f"Waited time: {waited_time}\n")
        return True

    def run(self, max_pod_creation_time_in_seconds) -> bool:
        initial_amount_of_nodes = len(self._nodes_finder.find_by_label_selector())
        logger.info(f"Initial amount of nodes: {initial_amount_of_nodes}")

        i = 1
        while True:
            pod_name = f"test-pod-{i}"
            initial_pods_map = self._over_provisioning_pods_finder.find_pods()
            if not self._create_pod_and_until_ready(
                    pod_name, max_pod_creation_time_in_seconds
            ):
                test_result = False
                break

            current_pods_map = self._over_provisioning_pods_finder.find_pods()

            if self.does_pods_changed_nodes(initial_pods_map, current_pods_map):
                test_result = True
                break

            if self._pods_to_create_quantity:
                if i > self._pods_to_create_quantity:
                    logger.info(
                        "Finish the test because of hit the limit of pods quantity"
                    )
                    test_result = False
                    break

            i += 1

        amount_of_nodes_after_test = len(self._nodes_finder.find_by_label_selector())
        logger.info(f"Amount of nodes after the test: {amount_of_nodes_after_test}")
        return test_result

    @staticmethod
    def does_pods_changed_nodes(initial_pods_nodes_map, current_pods_nodes_map):
        import json
        import sys

        for pod_name, node_name in current_pods_nodes_map.items():
            initial_node_name = initial_pods_nodes_map.get(pod_name)
            if not initial_node_name:
                logger.info(
                    f"Found diff between pods(with nodes) before pod creation and after"
                )
                logger.info(f"Current node_name:{node_name}, current_pod_name: {pod_name}")
                logger.info(f"Current node_name type:{type(node_name)}, current_pod_name type: {type(pod_name)}")

                logger.info(f"Before: \n{json.dumps(initial_pods_nodes_map)}\n")
                logger.info(f"After: \n{json.dumps(current_pods_nodes_map)}\n")
                logger.critical("Found over pods changed. Not expected behaviour")
                sys.exit(1)

            if initial_node_name != node_name:
                logger.info(
                    f"Pod with name: {pod_name} change his node."
                    f" The initial node: {initial_node_name}, current value: {node_name}"
                )
                # todo: check value of node_name field when node is not setuped
                if node_name is None:
                    raise NotImplementedError("Implement wait until nodes setuped")
                return True
        return False


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
