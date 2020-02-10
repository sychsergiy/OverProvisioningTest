from kubernetes import client

from over_provisioning.utils import pinpoint_execution_time


class PodCreator:
    def __init__(self, kuber: client.CoreV1Api, namespace: str, ):
        self._kuber = kuber
        self._namespace = namespace

    @pinpoint_execution_time
    def create_pod(self, pod_name: str, pod_spec: client.V1PodSpec):
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name),
            spec=pod_spec,
        )
        return self._kuber.create_namespaced_pod(self._namespace, pod, pretty=True)

