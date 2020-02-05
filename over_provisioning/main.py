from over_provisioning.kuber_namespace import KuberNamespace
from over_provisioning.nodes_finder import NodesFinder
from over_provisioning.pod_creator import PodCreator
from over_provisioning.pods_finder import LabeledPodsFinder
from over_provisioning.settings import Settings
from over_provisioning.test import create_kuber, OverProvisioningTest, run_test


def main(
        kubernetes_conf_path: str,
        kubernetes_namespace: str,
        max_pod_creation_time: float,
        over_provisioning_pods_label_selector: str,
        nodes_label_selector: str,
        create_new_namespace: bool,
        pods_to_create_quantity: int,
):
    settings = Settings(
        kubernetes_namespace,
        max_pod_creation_time,
        nodes_label_selector,
        over_provisioning_pods_label_selector,
    )
    kuber = create_kuber(kubernetes_conf_path)

    kubernetes_namespace_instance = KuberNamespace(kuber, kubernetes_namespace)
    over_provisioning_pods_finder = LabeledPodsFinder(
        kuber,
        namespace=settings.kubernetes_namespace,
        label_selector=settings.over_provisioning_pods_label_selector,
    )
    pod_creator = PodCreator(kuber, settings.kubernetes_namespace)
    nodes_finder = NodesFinder(kuber, settings.nodes_label_selector)

    test_runner = OverProvisioningTest(
        pod_creator,
        over_provisioning_pods_finder,
        nodes_finder,
        pods_to_create_quantity,
    )

    run_test(
        kubernetes_namespace_instance,
        create_new_namespace,
        test_runner,
        settings.max_pod_creation_time_in_seconds,
    )
