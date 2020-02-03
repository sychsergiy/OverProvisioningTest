class SettingsNoneAttributeException(Exception):
    def __init__(self, attribute_name):
        self.attribute_name = attribute_name

    def __str__(self):
        command_option = self.construct_option_name(self.attribute_name)
        env_var = self.construct_env_var_name(self.attribute_name)
        return (
            f"Settings attribute {self.attribute_name} can not be None.\n"
            f" Provide env var {env_var} or command option {command_option}"
        )

    @staticmethod
    def construct_option_name(attribute_name: str) -> str:
        return "--" + '-'.join(attribute_name.split("_"))

    @staticmethod
    def construct_env_var_name(attribute_name: str) -> str:
        return attribute_name.upper()


class Settings:
    def __init__(
            self,
            kubernetes_namespace: str,
            max_pod_creation_time_in_seconds: float,
            nodes_label_selector: str
    ):
        self.kubernetes_namespace = kubernetes_namespace
        self.max_pod_creation_time_in_seconds = max_pod_creation_time_in_seconds
        self.nodes_label_selector = nodes_label_selector

    @property
    def kubernetes_namespace(self):
        return self._kubernetes_namespace

    @kubernetes_namespace.setter
    def kubernetes_namespace(self, value):
        self._validate_not_none(value, "kubernetes_namespace")
        self._kubernetes_namespace = value

    @property
    def max_pod_creation_time_in_seconds(self):
        return self._max_pod_creation_time_in_seconds

    @max_pod_creation_time_in_seconds.setter
    def max_pod_creation_time_in_seconds(self, value):
        self._validate_not_none(value, "max_pod_creation_time_in_seconds")
        self._max_pod_creation_time_in_seconds = value

    @property
    def nodes_label_selector(self):
        return self._nodes_label_selector

    @nodes_label_selector.setter
    def nodes_label_selector(self, value):
        self._validate_not_none(value, "nodes_label_selector")
        self._nodes_label_selector = value

    @staticmethod
    def _validate_not_none(value, attribute_name: str):
        if value is None:
            raise SettingsNoneAttributeException(attribute_name)
