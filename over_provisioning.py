import typing as t
import time
import logging

import kubernetes.client.rest

from pprint import pprint

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


def create_namespace(kuber: client.CoreV1Api, namespace: str):
    return kuber.create_namespace(
        client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
    )


def list_nodes_filtered_by_label_selector(kuber: client.CoreV1Api, label_selector: str):
    """
    label_selector variations:
      only label key: "label_key"
      label key with value: "label_key=label_value"
      list of mixed labels: "label_key,label_key_2=label_value"
    """
    nodes = kuber.list_node(label_selector=label_selector)
    return nodes.items


def list_all_nodes(kuber: client.CoreV1Api):
    nodes = kuber.list_node()
    return nodes.items


def count_nodes_on_cluster(kuber: client.CoreV1Api) -> int:
    return len(list_all_nodes(kuber))


def count_nodes_by_label_selector(kuber: client.CoreV1Api, label_selector: str):
    return len(list_nodes_filtered_by_label_selector(kuber, label_selector))


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

    def is_exists(self):
        try:
            self._kuber.read_namespace(self._name)
        except client.rest.ApiException as e:
            if e.status == 404:
                return False
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
        # todo: use node name instead of host_IP
        return {pod.metadata.name: pod.status.host_ip for pod in pods_list.items}


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


def test_over_provisioning(
        kuber: client.CoreV1Api, pods_creator: PodsCreator,
        over_provisioning_pods_finder: OverProvisioningPodsFinder,
        settings: Settings
):
    initial_amount_of_nodes = count_nodes_on_cluster(kuber)
    logger.info(f"Initial amount of nodes: {initial_amount_of_nodes}")
    pods_map = over_provisioning_pods_finder.find_pods()

    i = 1
    while i < 10:  # todo: infinity instead of 10 here
        pod_name = f"test-pod-{i}"
        logger.info(f"Init pod creation. Pod name: {pod_name}")
        _, execution_time = pods_creator.create_pod(pod_name)
        logger.info(f"Pod creation time: {execution_time}")

        if execution_time > settings.max_pod_creation_time_in_seconds:
            logger.info("Pod creation time hit the limit. Test Failed")
            return

        logger.info(f"Wait until pod is ready")
        _, waited_time = pods_creator.wait_until_pod_ready(pod_name)
        logger.info(f"Waited time: {waited_time}\n")

        pods_map_after_pod_creation = over_provisioning_pods_finder.find_pods()

        if pods_map != pods_map_after_pod_creation:
            logger.info(f"One of the over provisioning pods changed the node")  # should not be triggered locally
            return

        i += 1

    amount_of_nodes_after_test = count_nodes_on_cluster(kuber)
    logger.info(f"Amount of nodes after the test: {amount_of_nodes_after_test}")


def delete_namespace(kuber: client.CoreV1Api, namespace: str):
    kuber.delete_namespace(namespace)


def is_namespace_exists(kuber: client.CoreV1Api, name: str) -> bool:
    try:
        kuber.read_namespace(name)
    except client.rest.ApiException as e:
        if e.status == 404:
            return False
        else:
            raise e
    return True


def main(settings: Settings, kuber_config_file_path: str, kuber_namespace: KuberNamespace, create_new_namespace: bool):
    kuber = create_kuber(kuber_config_file_path)
    if create_new_namespace:
        kuber_namespace.create()
        time.sleep(1)
    else:
        if not kuber_namespace.is_exists():
            raise RuntimeError(f"Provided namespace: {settings.kubernetes_namespace} doesnt exists.")

    over_provisioning_pods_finder = LabeledPodsFinder(
        kuber, namespace=settings.kubernetes_namespace,
        label_selector=settings.nodes_label_selector
    )
    pods_creator = PodsCreator(kuber, settings.kubernetes_namespace)
    test_over_provisioning(kuber, pods_creator, over_provisioning_pods_finder, settings)

    kuber_namespace.delete()
