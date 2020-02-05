from over_provisioning.environment_setuper import (
    EnvironmentSetuper,
    CreateNamespaceHook,
    DeleteNamespaceHook,
    CheckNamespaceExistsHook,
)
from over_provisioning.kuber_namespace import KuberNamespace
from over_provisioning.nodes_finder import NodesFinder
from over_provisioning.pod_creator import PodCreator
from over_provisioning.pods_finder import LabeledPodsFinder
from over_provisioning.settings import Settings
from over_provisioning.test import create_kuber, OneOverProvisioningPodTest, run_test, PodCreatingLoop


def main(
        kubernetes_conf_path: str,
        kubernetes_namespace: str,
        max_pod_creation_time: float,
        over_provisioning_pods_label_selector: str,
        over_provisioning_pods_namespace: str,
        nodes_label_selector: str,
        create_new_namespace: bool,
        pods_to_create_quantity: int,
):
    settings = Settings(
        kubernetes_namespace,
        max_pod_creation_time,
        nodes_label_selector,
        over_provisioning_pods_label_selector,
        over_provisioning_pods_namespace
    )
    kuber = create_kuber(kubernetes_conf_path)

    kubernetes_namespace_instance = KuberNamespace(kuber, kubernetes_namespace)
    over_provisioning_pods_finder = LabeledPodsFinder(
        kuber,
        namespace=settings.over_provisioning_pods_namespace,
        label_selector=settings.over_provisioning_pods_label_selector,
    )
    pod_creator = PodCreator(kuber, settings.kubernetes_namespace)
    nodes_finder = NodesFinder(kuber, settings.nodes_label_selector)

    pod_creating_loop = PodCreatingLoop(
        pod_creator, over_provisioning_pods_finder, nodes_finder, pods_to_create_quantity
    )

    env_setuper = EnvironmentSetuper()
    if create_new_namespace:
        env_setuper.add_create_hook(CreateNamespaceHook(kubernetes_namespace_instance))
        env_setuper.add_destroy_hook(DeleteNamespaceHook(kubernetes_namespace_instance))
    else:
        env_setuper.add_create_hook(CheckNamespaceExistsHook(kubernetes_namespace_instance))

    test_runner = OneOverProvisioningPodTest(
        pod_creating_loop,
        nodes_finder,
        env_setuper
    )

    run_test(test_runner, max_pod_creation_time)
