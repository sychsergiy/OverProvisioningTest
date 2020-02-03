class Settings:
    def __init__(
        self,
        kubernetes_namespace: str,
        max_pod_creation_time_in_seconds: float,
        nodes_label_selector: str
    ):
        self.KUBERNETES_NAMESPACE = kubernetes_namespace
        self.MAX_POD_CREATION_TIME_IN_SECONDS = max_pod_creation_time_in_seconds
        self.NODES_LABEL_SELECTOR = nodes_label_selector
