import typing as t

from kubernetes import client


class PodDeleter:
    def __init__(self, kuber: client.CoreV1Api, namespace: str):
        self._kuber = kuber
        self._namespace = namespace

    def delete_one(self, pod_name: str):
        self._kuber.delete_namespaced_pod(pod_name, self._namespace)

    def delete_many(self, pods_names: t.List[str]):
        for pod_name in pods_names:
            self.delete_one(pod_name)

    def delete_all(self):
        self._kuber.delete_collection_namespaced_pod(self._namespace)
