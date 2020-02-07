import time
import typing as t
import logging

from kubernetes import client

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Pod(t.NamedTuple):
    name: str
    node_name: str


class OverProvisioningPodsFinder:
    def find_pods(self) -> t.List[Pod]:
        """
        map where key is pod name, value is node name
        """
        raise NotImplementedError()

    def wait_until_node_assigned(self, pod_name: str):
        raise NotImplementedError()


class LabeledPodsFinder(OverProvisioningPodsFinder):
    def __init__(self, kuber: client.CoreV1Api, namespace: str, label_selector: str):
        self._kuber = kuber
        self._label_selector = label_selector
        self._namespace = namespace

    def find_pods(self) -> t.List[Pod]:
        pods_list: client.models.v1_pod_list.V1PodList = self._kuber.list_namespaced_pod(
            self._namespace, label_selector=self._label_selector
        )
        return [Pod(pod.metadata.name, pod.spec.node_name) for pod in pods_list.items]

    def wait_until_node_assigned(self, pod_name: str):
        waited_time_sum = 0
        while True:
            pod = self._kuber.read_namespaced_pod(pod_name, self._namespace)
            if not self.is_node_assigned(pod):
                time.sleep(1)
                waited_time_sum += 1
            else:
                logger.info(f"Totally waited on node assigning: {waited_time_sum}")
                return

    @staticmethod
    def is_node_assigned(pod) -> bool:
        return pod.spec.node_name is not None
