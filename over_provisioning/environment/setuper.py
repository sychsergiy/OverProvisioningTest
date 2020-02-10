import typing as t

from over_provisioning.environment.hooks import EnvironmentHook


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
