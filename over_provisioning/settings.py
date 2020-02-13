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
        return "--" + "-".join(attribute_name.split("_"))

    @staticmethod
    def construct_env_var_name(attribute_name: str) -> str:
        return attribute_name.upper()


class Settings:
    def __init__(
        self,
        kubernetes_namespace: str,
        max_pod_creation_time_in_seconds: float,
        nodes_label_selector: str,
        over_provisioning_pods_label_selector: str,
        over_provisioning_pods_namespace: str,
        pods_to_create_quantity: int,
        max_amount_of_nodes: int,
        max_nodes_assigning_time: int,
    ):
        self.kubernetes_namespace = kubernetes_namespace
        self.max_pod_creation_time_in_seconds = max_pod_creation_time_in_seconds
        self.nodes_label_selector = nodes_label_selector
        self.over_provisioning_pods_label_selector = (
            over_provisioning_pods_label_selector
        )
        self.over_provisioning_pods_namespace = over_provisioning_pods_namespace
        self.pods_to_create_quantity = pods_to_create_quantity
        self.max_amount_of_nodes = max_amount_of_nodes
        self.max_nodes_assigning_time = max_nodes_assigning_time

    @property
    def max_nodes_assigning_time(self):
        return self._max_nodes_assigning_time

    @max_nodes_assigning_time.setter
    def max_nodes_assigning_time(self, value):
        self._validate_not_none(value, "max_nodes_assigning_time")
        self._max_nodes_assigning_time = value

    @property
    def max_amount_of_nodes(self):
        return self._max_amount_of_nodes

    @max_amount_of_nodes.setter
    def max_amount_of_nodes(self, value):
        self._validate_not_none(value, "max_amount_of_nodes")
        self._max_amount_of_nodes = value

    @property
    def pods_to_create_quantity(self):
        return self._pods_to_create_quantity

    @pods_to_create_quantity.setter
    def pods_to_create_quantity(self, value):
        # can be empty
        self._pods_to_create_quantity = value

    @property
    def over_provisioning_pods_namespace(self):
        return self._over_provisioning_pods_namespace

    @over_provisioning_pods_namespace.setter
    def over_provisioning_pods_namespace(self, value):
        self._validate_not_none(value, "over_provisioning_pods_label_selector")
        self._over_provisioning_pods_namespace = value

    @property
    def over_provisioning_pods_label_selector(self):
        return self._over_provisioning_pods_label_selector

    @over_provisioning_pods_label_selector.setter
    def over_provisioning_pods_label_selector(self, value):
        self._validate_not_none(value, "over_provisioning_pods_label_selector")
        self._over_provisioning_pods_label_selector = value

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
