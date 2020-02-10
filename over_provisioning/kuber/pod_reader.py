from kubernetes import client


class PodReader:
    def __init__(self, kuber: client.CoreV1Api, namespace: str):
        self._kuber = kuber
        self._namespace = namespace

    def read(self, pod_name: str):
        return self._kuber.read_namespaced_pod(pod_name, self._namespace)
