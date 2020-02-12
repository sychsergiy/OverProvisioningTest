import time

from over_provisioning.kuber.namespace import KuberNamespace
from over_provisioning.kuber.pod_deleter import PodDeleter


class EnvironmentHook:
    def run(self):
        raise NotImplementedError


class CreateNamespaceHook(EnvironmentHook):
    def __init__(self, kuber_namespace: KuberNamespace):
        self._kuber_namespace = kuber_namespace

    def run(self):
        self._kuber_namespace.create()
        time.sleep(2)


class CheckNamespaceExistsHook(EnvironmentHook):
    def __init__(self, kuber_namespace: KuberNamespace):
        self._kuber_namespace = kuber_namespace

    def run(self):
        self._kuber_namespace.check_if_exists()


class DeleteNamespaceHook(EnvironmentHook):
    def __init__(self, kuber_namespace: KuberNamespace):
        self._kuber_namespace = kuber_namespace

    def run(self):
        self._kuber_namespace.delete()


class CleanupAllPodsInNamespaceHook(EnvironmentHook):
    def __init__(self, pods_deleter: PodDeleter):
        self._pods_deleter = pods_deleter

    def run(self):
        self._pods_deleter.delete_all()
