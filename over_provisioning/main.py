import sys

from over_provisioning.environment.setuper import (
    EnvironmentSetuper,

)
from over_provisioning.environment.hooks import (
    CreateNamespaceHook,
    DeleteNamespaceHook,
    CheckNamespaceExistsHook,
)
from over_provisioning.kuber import factory
from over_provisioning.kuber.namespace import KuberNamespace
from over_provisioning.kuber.pod_creator import PodCreator
from over_provisioning.kuber.pod_deleter import PodDeleter
from over_provisioning.kuber.nodes_finder import NodesFinder
from over_provisioning.kuber.pod_reader import PodReader
from over_provisioning.logger import get_logger
from over_provisioning.pods_finder import LabeledPodsFinder
from over_provisioning.settings import Settings
from over_provisioning.test.pod_creating_loop import PodCreatingLoop
from over_provisioning.test.node_assigning_waiter import NodesAssigningWaiter
from over_provisioning.test.pod_waiter import PodWaiter
from over_provisioning.test.pods_cleaner import PodsCleaner
from over_provisioning.test.pods_spawner import PodsSpawner
from over_provisioning.pod_specs import local_development_pod_spec, eks_development_pod_spec
from over_provisioning.test.pods_state_checker import OverProvisioningPodsStateChecker
from over_provisioning.test.runner import OneOverProvisioningPodTest

logger = get_logger()


def run_test(
        over_provisioning_test: OneOverProvisioningPodTest,
        max_pod_creation_time_in_seconds: float,
):
    result = over_provisioning_test.run(max_pod_creation_time_in_seconds)

    if result:
        logger.info("Test pass ......................")
        sys.exit(0)
    else:
        logger.info("Test failed ....................")
        sys.exit(1)


def main(
        kubernetes_conf_path: str,
        kubernetes_namespace: str,
        max_pod_creation_time: float,
        over_provisioning_pods_label_selector: str,
        over_provisioning_pods_namespace: str,
        nodes_label_selector: str,
        create_new_namespace: bool,
        pods_to_create_quantity: int,
        local_development: bool
):
    settings = Settings(
        kubernetes_namespace,
        max_pod_creation_time,
        nodes_label_selector,
        over_provisioning_pods_label_selector,
        over_provisioning_pods_namespace,
        pods_to_create_quantity,
    )
    kuber = factory.create_kuber(kubernetes_conf_path)

    kubernetes_namespace_instance = KuberNamespace(kuber, kubernetes_namespace)
    over_provisioning_pods_finder = LabeledPodsFinder(
        kuber,
        namespace=settings.over_provisioning_pods_namespace,
        label_selector=settings.over_provisioning_pods_label_selector,
    )
    pod_creator = PodCreator(kuber, settings.kubernetes_namespace)
    nodes_finder = NodesFinder(kuber, settings.nodes_label_selector)

    pod_waiter = PodWaiter(
        PodReader(kuber, settings.kubernetes_namespace),
        0.5,  # read pod status with 0.5 seconds interval
    )
    node_assigning_waiter = NodesAssigningWaiter(
        PodReader(kuber, settings.over_provisioning_pods_namespace),
        60 * 15,  # 60 wait on nodes assigning for 15 minutes
    )

    pod_spec = local_development_pod_spec if local_development else eks_development_pod_spec

    pods_spawner = PodsSpawner(pod_creator, pod_waiter, "test-pod", pod_spec)
    over_provisioning_pods_state_checker = OverProvisioningPodsStateChecker(
        over_provisioning_pods_finder, node_assigning_waiter
    )
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

    pods_cleaner = PodsCleaner(pod_deleter)
    test_runner = OneOverProvisioningPodTest(
        pod_creating_loop, nodes_finder, env_setuper, pods_cleaner,
    )

    run_test(test_runner, settings.max_pod_creation_time_in_seconds)
