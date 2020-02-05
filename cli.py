import click

from over_provisioning.kuber_namespace import KuberNamespace
from over_provisioning.test_runner import (
    main,
    create_kuber,
    OverProvisioningTestRunner,
)
from over_provisioning.pod_creator import PodCreator
from over_provisioning.pods_finder import LabeledPodsFinder
from over_provisioning.nodes_finder import NodesFinder
from over_provisioning.settings import Settings


@click.command()
@click.argument(
    "kubernetes_conf_path", envvar="KUBERNETES_CONF_PATH", type=click.Path(exists=True),
)
@click.option(
    "-n",
    "--kubernetes-namespace",
    envvar="KUBERNETES_NAMESPACE",
    type=click.STRING,
    help="Namespace where over provisioning test will be executed",
)
@click.option(
    "--create-new-namespace/--no-create-new-namespace",
    default=True,
    help="Create new kubernetes namespace or use existent. By default True",
)
@click.option(
    "-t",
    "--max-pod-creation-time",
    envvar="MAX_POD_CREATION_TIME_IN_SECONDS",
    type=click.FLOAT,
    help="Max time for pod creation in seconds. If pod creation hit this limit test will fail",
)
@click.option(
    "-l",
    "--over-provisioning-pods-label-selector",
    envvar="OVER_PROVISIONING_PODS_LABEL_SELECTOR",
    type=click.STRING,
    help="Set label selector to find over provisioning pods",
)
@click.option(
    "-s",
    "--nodes-label-selector",
    envvar="NODES_LABEL_SELECTOR",
    type=click.STRING,
    help="Label selector to filter nodes",
)
@click.option(
    "-p",
    "--pods-to-create-quantity",
    type=click.INT,
    default=None,
    help="Quantity pods to create before finishing test. Created only for local running(to finish test)",
)
def run(
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

    test_runner = OverProvisioningTestRunner(
        pod_creator,
        over_provisioning_pods_finder,
        nodes_finder,
        pods_to_create_quantity,
    )

    main(
        kubernetes_namespace_instance,
        create_new_namespace,
        test_runner,
        settings.max_pod_creation_time_in_seconds,
    )


if __name__ == "__main__":
    run()
