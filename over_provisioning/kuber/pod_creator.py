from kubernetes import client

from over_provisioning.timer import Timer


class PodCreator:
    def __init__(
        self, kuber: client.CoreV1Api, namespace: str,
    ):
        self._kuber = kuber
        self._namespace = namespace

    def create_pod(self, pod_name: str, pod_spec: client.V1PodSpec) -> float:
        with Timer() as timer:
            pod = client.V1Pod(
                metadata=client.V1ObjectMeta(name=pod_name), spec=pod_spec,
            )
            self._kuber.create_namespaced_pod(self._namespace, pod)
        return timer.elapsed
