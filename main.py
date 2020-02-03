import typing as t
import time
import logging

from kubernetes import client, config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
NAMESPACE = "test-ns"


class Config:
    AMOUNT_OF_PODS_TO_CREATE = 10
    MAX_POD_CREATION_TIME_IN_SECONDS = 10
    NAMESPACE = "test-ns"
    NODES_LABEL_SELECTOR = "test-tag"


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


@pinpoint_execution_time
def create_pod(kuber: client.CoreV1Api, namespace: str, pod_name: str):
    pod = client.V1Pod(
        metadata=client.V1ObjectMeta(name=pod_name),
        spec=client.V1PodSpec(
            containers=[client.V1Container(name="test", image="nginx")]
        ),
    )
    return kuber.create_namespaced_pod(namespace, pod, pretty=True)


def list_nodes_filtered_by_label_selector(kuber: client.CoreV1Api, label_selector: str):
    """
    label_selector variations:
      only label key: "label_key"
      label key with value: "label_key=label_value"
      list of mixed labels: "label_key,label_key_2=label_value"
    """
    nodes = kuber.list_node(label_selector=label_selector)
    return nodes.items


def count_nodes_by_label_selector(kuber: client.CoreV1Api, label_selector: str):
    return len(list_nodes_filtered_by_label_selector(kuber, label_selector))


def is_pod_ready(pod) -> bool:
    if not pod.status.conditions:
        return False
    statuses = [item.type for item in pod.status.conditions]
    return "Ready" in statuses


@pinpoint_execution_time
def wait_until_pod_is_ready(kuber: client.CoreV1Api, namespace: str, pod_name: str):
    # todo: add time expiration exception
    pod = kuber.read_namespaced_pod(pod_name, namespace)
    if not is_pod_ready(pod):
        time.sleep(0.1)


def test_over_provisioning(
        kuber: client.CoreV1Api, configuration):
    initial_amount_of_nodes = count_nodes_by_label_selector(kuber, configuration.NODES_LABEL_SELECTOR)

    for i in range(1, configuration.AMOUNT_OF_PODS_TO_CREATE + 1):
        pod_name = f"test-pod-{i}"
        logger.info(f"Init pod creation. Pod name: {pod_name}")
        _, execution_time = create_pod(kuber, configuration.NAMESPACE, pod_name)
        logger.info(f"Pod creation time: {execution_time}")
        logger.info(f"Wait until pod is ready")
        _, waited_time = wait_until_pod_is_ready(kuber, configuration.NAMESPACE, pod_name)
        logger.info(f"Waited time: {waited_time}\n")

        if execution_time > configuration.MAX_POD_CREATION_TIME_IN_SECONDS:
            logger.info("Pod creation time hit the limit. Test Failed")
            return False

        nodes_amount = count_nodes_by_label_selector(kuber, configuration.NODES_LABEL_SELECTOR)
        if nodes_amount > initial_amount_of_nodes:
            logger.info(f"Amount of nodes increased. Test Passed")
            return True

    logger.info(
        f"{configuration.AMOUNT_OF_PODS_TO_CREATE} pods created, but amount of nodes still the same. Test Failed."
    )
    cleanup_pods(kuber, configuration.AMOUNT_OF_PODS_TO_CREATE, configuration.NAMESPACE)
    return False


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


def test_over_provisioning_v2(kuber: client.CoreV1Api, over_provisioning_pods_finder: OverProvisioningPodsFinder,
                              configuration):
    initial_amount_of_nodes = count_nodes_by_label_selector(kuber, configuration.NODES_LABEL_SELECTOR)
    logger.info(f"Initial amount of nodes: {initial_amount_of_nodes}")
    pods_map = over_provisioning_pods_finder.find_pods()

    i = 1
    while i < 10:  # todo: infinity instead of 10 here
        pod_name = f"test-pod-{i}"
        logger.info(f"Init pod creation. Pod name: {pod_name}")
        _, execution_time = create_pod(kuber, configuration.NAMESPACE, pod_name)
        logger.info(f"Pod creation time: {execution_time}")

        if execution_time > configuration.MAX_POD_CREATION_TIME_IN_SECONDS:
            logger.info("Pod creation time hit the limit. Test Failed")
            return

        logger.info(f"Wait until pod is ready")
        _, waited_time = wait_until_pod_is_ready(kuber, configuration.NAMESPACE, pod_name)
        logger.info(f"Waited time: {waited_time}\n")

        pods_map_after_pod_creation = over_provisioning_pods_finder.find_pods()

        if pods_map != pods_map_after_pod_creation:
            logger.info(f"One of the over provisioning pods changed the node")  # should not be triggered locally
            return

        i += 1

    amount_of_nodes_after_test = count_nodes_by_label_selector(kuber, configuration.NODES_LABEL_SELECTOR)
    logger.info(f"Amount of nodes after the test: {amount_of_nodes_after_test}")


def cleanup_pods(kuber: client.CoreV1Api, pods_names: t.List[str], namespace: str):
    for pod_name in pods_names:
        kuber.delete_namespaced_pod(pod_name, namespace)


def delete_namespace(kuber: client.CoreV1Api, namespace: str):
    kuber.delete_namespace(namespace)


def main():
    kuber_config_file_path = "kube_config.yaml"
    kuber = create_kuber(kuber_config_file_path)

    create_namespace(kuber, Config.NAMESPACE)

    time.sleep(2)

    pods_finder = LabeledPodsFinder(kuber, namespace=Config.NAMESPACE, label_selector=Config.NODES_LABEL_SELECTOR)
    test_over_provisioning_v2(kuber, pods_finder, Config)

    delete_namespace(kuber, Config.NAMESPACE)


if __name__ == "__main__":
    main()
