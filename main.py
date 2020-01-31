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
    NODE_TAG = "test-tag"


def pinpoint_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        func_execution_time = end_time - start_time
        return result, func_execution_time

    return wrapper


def create_kuber():
    # connect to Cluster with IAM
    config.load_kube_config()
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


def list_nodes_with_tag(kuber: client.CoreV1Api, tag: str):
    nodes = kuber.list_node()
    # todo: filter by tag
    return nodes.items


def count_nodes_with_tag(kuber: client.CoreV1Api, tag: str):
    return len(list_nodes_with_tag(kuber, tag))


def is_pod_ready(pod):
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
    initial_amount_of_nodes = count_nodes_with_tag(kuber, configuration.NODE_TAG)

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

        nodes_amount = count_nodes_with_tag(kuber, configuration.NODE_TAG)
        logger.info(f"Pod creation time hit the limit. Test Failed")
        if nodes_amount > initial_amount_of_nodes:
            logger.info(f"Amount of nodes increased. Test Passed")
            return True

    logger.info(
        f"{configuration.AMOUNT_OF_PODS_TO_CREATE} pods created, but amount of nodes still the same. Test Failed."
    )
    cleanup_pods(kuber, configuration.AMOUNT_OF_PODS_TO_CREATE, configuration.NAMESPACE)
    return False


def cleanup_pods(kuber: client.CoreV1Api, pods_amount: int, namespace: str):
    for i in range(1, pods_amount + 1):
        pod_name = f"test-pod-{i}"
        kuber.delete_namespaced_pod(pod_name, namespace)


def main():
    kuber = create_kuber()
    result = test_over_provisioning(kuber, Config)
    print(result)


if __name__ == "__main__":
    main()
