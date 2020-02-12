import typing as t

from over_provisioning.environment.hooks import EnvironmentHook
from over_provisioning.logger import get_logger

logger = get_logger()


class EnvironmentSetuper:
    def __init__(
        self,
        create_hooks: t.List[EnvironmentHook] = None,
        destroy_hooks: t.List[EnvironmentHook] = None,
    ):
        self._create_hooks = create_hooks or []
        self._destroy_hooks = destroy_hooks or []

    def add_create_hook(self, hook: EnvironmentHook):
        self._create_hooks.append(hook)

    def add_destroy_hook(self, hook: EnvironmentHook):
        self._destroy_hooks.append(hook)

    def __enter__(self):
        return self.create()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy()
        if exc_type is not None:
            return False  # reraise exception

    def create(self) -> bool:
        try:
            logger.info("Trying to create environment")
            for hook in self._create_hooks:
                hook.run()
            logger.info("Environment successfully created")
            return True
        except Exception:
            logger.exception(
                "Failed to setup environment due to the following exception."
            )
            return False

    def destroy(self) -> bool:
        try:
            logger.info("Trying to destroy environment")
            for hook in self._destroy_hooks:
                hook.run()
            logger.info("Environment successfully destroyed")
            return True
        except Exception:
            logger.exception(
                "Failed to destroy environment due to the following exception."
            )
            logger.info("Manual environment cleanup required")
            return False
