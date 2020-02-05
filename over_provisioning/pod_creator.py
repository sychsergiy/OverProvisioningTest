import time

from kubernetes import client

from over_provisioning.utils import pinpoint_execution_time


class PodCreator:
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
