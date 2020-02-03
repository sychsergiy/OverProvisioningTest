import typing as t
import time
import logging

import kubernetes.client.rest

from kubernetes import client, config

from settings import Settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def pinpoint_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        func_execution_time = end_time - start_time
        return result, func_execution_time

    return wrapper


def create_kuber(config_file_path=None):
    config.load_kube_config(config_file_path)
    kuber = client.CoreV1Api()
    return kuber


class NodesLister:
    def __init__(self, kuber: client.CoreV1Api):
        self._kuber = kuber

    def find_by_label_selector(self, label_selector: str):
        """
        label_selector variations:
          only label key: "label_key"
          label key with value: "label_key=label_value"
          list of mixed labels: "label_key,label_key_2=label_value"
        """
        nodes = self._kuber.list_node(label_selector=label_selector)
        return nodes.items

    def find_all(self):
        nodes = self._kuber.list_node()
        return nodes.items


class KuberNamespace:
    def __init__(self, kuber: client.CoreV1Api, name: str):
        self._kuber = kuber
        self._name = name

    def create(self):
        return self._kuber.create_namespace(
            client.V1Namespace(metadata=client.V1ObjectMeta(name=self._name))
        )

    def delete(self):
        return self._kuber.delete_namespace(self._name)

    def check_if_exists(self):
        try:
            self._kuber.read_namespace(self._name)
        except client.rest.ApiException as e:
            if e.status == 404:
                raise RuntimeError(f"Provided namespace: {self._name} doesnt exists.")
            else:
                raise e
        return True


class OverProvisioningPodsFinder:
    def find_pods(self) -> t.Dict[str, str]:
        """
        map where key is pod name, value is node name
        """
        raise NotImplementedError()


class LabeledPodsFinder(OverProvisioningPodsFinder):
    def __init__(self, kuber: client.CoreV1Api, namespace: str, label_selector: str):
        self.kuber = kuber
        self.label_selector = label_selector
        self.namespace = namespace

    def find_pods(self) -> t.Dict[str, str]:
        pods_list: client.models.v1_pod_list.V1PodList = self.kuber.list_namespaced_pod(
            self.namespace, label_selector=self.label_selector
        )
        # todo: try to use node name instead of host_IP
        return {pod.metadata.name: pod.spec.node_name for pod in pods_list.items}


class PodsCreator:
    def __init__(self, kuber: client.CoreV1Api, namespace: str):
        self._kuber = kuber
        self._namespace = namespace

    @pinpoint_execution_time
    def create_pod(self, pod_name: str):
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name),
            spec=client.V1PodSpec(
                containers=[client.V1Container(name="test", image="nginx")]
            ),
        )
        return self._kuber.create_namespaced_pod(self._namespace, pod, pretty=True)

    @pinpoint_execution_time
    def wait_until_pod_ready(self, pod_name: str):
        pod = self._kuber.read_namespaced_pod(pod_name, self._namespace)
        if not self.is_pod_ready(pod):
            time.sleep(0.1)

    @staticmethod
    def is_pod_ready(pod) -> bool:
        if not pod.status.conditions:
            return False
        statuses = [item.type for item in pod.status.conditions]
        return "Ready" in statuses


class OverProvisioningTest:
    def __init__(
            self,
            pods_creator: PodsCreator,
            over_provisioning_pods_finder: OverProvisioningPodsFinder,
            nodes_lister: NodesLister,
    ):
        self._pods_creator = pods_creator
        self._over_provisioning_pods_finder = over_provisioning_pods_finder
        self._nodes_lister = nodes_lister

    def run(self, max_pod_creation_time_in_seconds):
        initial_amount_of_nodes = len(self._nodes_lister.find_all())
        logger.info(f"Initial amount of nodes: {initial_amount_of_nodes}")
        pods_map = self._over_provisioning_pods_finder.find_pods()

        i = 1
        while i < 30:  # todo: infinity instead of 10 here
            pod_name = f"test-pod-{i}"
            logger.info(f"Init pod creation. Pod name: {pod_name}")
            _, execution_time = self._pods_creator.create_pod(pod_name)
            logger.info(f"Pod creation time: {execution_time}")

            if execution_time > max_pod_creation_time_in_seconds:
                logger.info("Pod creation time hit the limit. Test Failed")
                return

            logger.info(f"Wait until pod is ready")
            _, waited_time = self._pods_creator.wait_until_pod_ready(pod_name)
            logger.info(f"Waited time: {waited_time}\n")

            pods_map_after_pod_creation = self._over_provisioning_pods_finder.find_pods()

            if self.does_pods_changed_pods(pods_map, pods_map_after_pod_creation):
                return True

            i += 1

        amount_of_nodes_after_test = len(self._nodes_lister.find_all())
        logger.info(f"Amount of nodes after the test: {amount_of_nodes_after_test}")

    @staticmethod
    def does_pods_changed_pods(initial_pods_nodes_map, pods_nodes_map):
        for pod_name, node_name in pods_nodes_map.items():
            initial_node_name = initial_pods_nodes_map[pod_name]
            if initial_node_name != node_name:
                logger.info(
                    f"Pod with name: {pod_name} change his node."
                    f" The initial node: {initial_node_name}, current value: {node_name}"
                )
                if node_name is None:  # todo: check value of node_name field when node is not setuped
                    raise NotImplementedError("Implement wait until nodes setuped")
                return True
        return False


def main(
        kuber_namespace: KuberNamespace,
        create_new_namespace: bool,
        test_runner: OverProvisioningTest,
        max_pod_creation_time_in_seconds: float,
):
    if create_new_namespace:
        kuber_namespace.create()
        time.sleep(1)
    else:
        kuber_namespace.check_if_exists()

    test_runner.run(max_pod_creation_time_in_seconds)
    kuber_namespace.delete()
