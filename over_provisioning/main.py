from over_provisioning.environment.setuper import (
    EnvironmentSetuper,

)
from over_provisioning.environment.hooks import (
    CreateNamespaceHook,
    DeleteNamespaceHook,
    CheckNamespaceExistsHook,
)

from over_provisioning.kuber.namespace import KuberNamespace
from over_provisioning.kuber.pod_creator import PodCreator
from over_provisioning.kuber.pod_deleter import PodDeleter
from over_provisioning.kuber.nodes_finder import NodesFinder
from over_provisioning.kuber.pod_reader import PodReader
from over_provisioning.pods_finder import LabeledPodsFinder
from over_provisioning.settings import Settings
from over_provisioning.test import create_kuber, OneOverProvisioningPodTest, run_test
from over_provisioning.tests.loop_v3 import PodCreatingLoop, OverProvisioningPodsStateChecker
from over_provisioning.tests.pod_waiter import PodWaiter
from over_provisioning.tests.pods_spawner import PodsSpawner
from over_provisioning.pod_specs import local_development_pod_spec


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
    pod_reader = PodReader(kuber, settings.kubernetes_namespace)
    nodes_finder = NodesFinder(kuber, settings.nodes_label_selector)

    pod_waiter = PodWaiter(pod_reader)

    pods_spawner = PodsSpawner(pod_creator, pod_waiter, "test-pod", local_development_pod_spec)
    over_provisioning_pods_state_checker = OverProvisioningPodsStateChecker(over_provisioning_pods_finder)
    pod_creating_loop = PodCreatingLoop(
        pods_spawner, over_provisioning_pods_state_checker,
        pods_to_create_quantity
    )

    env_setuper = EnvironmentSetuper()
    if create_new_namespace:
        env_setuper.add_create_hook(CreateNamespaceHook(kubernetes_namespace_instance))
        env_setuper.add_destroy_hook(DeleteNamespaceHook(kubernetes_namespace_instance))
    else:
        env_setuper.add_create_hook(CheckNamespaceExistsHook(kubernetes_namespace_instance))

    pod_deleter = PodDeleter(kuber, settings.kubernetes_namespace)

    test_runner = OneOverProvisioningPodTest(
        pod_creating_loop, nodes_finder, env_setuper, pod_deleter,
    )

    run_test(test_runner, settings.max_pod_creation_time_in_seconds)
