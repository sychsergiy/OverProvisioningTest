import time
import typing as t

from over_provisioning.kuber_namespace import KuberNamespace


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


class CleanupPodHook(EnvironmentHook):
    def __init__(self, pods_to_delete: t.List[str]):
        self._pods_to_delete = pods_to_delete

    def run(self):
        pass


class EnvironmentSetuper:
    def __init__(self, create_hooks: t.List[EnvironmentHook] = None, destroy_hooks: t.List[EnvironmentHook] = None):
        # both properties can injected, that's fields are public
        self._create_hooks = create_hooks or []
        self._destroy_hooks = destroy_hooks or []

    def add_create_hook(self, hook: EnvironmentHook):
        self._create_hooks.append(hook)

    def add_destroy_hook(self, hook: EnvironmentHook):
        self._destroy_hooks.append(hook)

    def create(self):
        for hook in self._create_hooks:
            hook.run()

    def destroy(self):
        for hook in self._destroy_hooks:
            hook.run()
