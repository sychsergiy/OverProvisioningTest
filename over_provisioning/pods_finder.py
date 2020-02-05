import typing as t

from kubernetes import client


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
