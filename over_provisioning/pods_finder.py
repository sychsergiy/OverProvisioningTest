import typing as t

from kubernetes import client

from over_provisioning.logger import get_logger

logger = get_logger()


class Pod(t.NamedTuple):
    name: str
    node_name: str


class OverProvisioningPodsFinder:
    def find_pods(self) -> t.List[Pod]:
        """
        map where key is pod name, value is node name
        """
        raise NotImplementedError()


class LabeledPodsFinder(OverProvisioningPodsFinder):
    def __init__(
        self, kuber: client.CoreV1Api, namespace: str, label_selector: str
    ):
        self._kuber = kuber
        self._label_selector = label_selector
        self._namespace = namespace

    def find_pods(self) -> t.List[Pod]:
        pods_list: client.models.v1_pod_list.V1PodList = self._kuber.list_namespaced_pod(
            self._namespace, label_selector=self._label_selector
        )
        return [
            Pod(pod.metadata.name, pod.spec.node_name)
            for pod in pods_list.items
        ]
