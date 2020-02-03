import click

from over_provisioning import main, KuberNamespace, create_kuber, PodsCreator, LabeledPodsFinder, NodesLister, \
    OverProvisioningTest

from settings import Settings


@click.command()
@click.argument(
    "kubernetes_conf_path", envvar="KUBERNETES_CONF_PATH", type=click.Path(exists=True),
)
@click.option(
    "-n", "--kubernetes-namespace", envvar="KUBERNETES_NAMESPACE", type=click.STRING,
    help="Namespace where over provisioning test will be executed"
)
@click.option(
    "--create-new-namespace/--no-create-new-namespace", default=True,
    help="Create new kubernetes namespace. If not set, test will try to find existent. By default True",
)
@click.option(
    "-t", "--max-pod-creation-time", envvar="MAX_POD_CREATION_TIME", type=click.FLOAT,
    help="Max time for pod creation in seconds. If pod creation hit this limit test will fail"
)
@click.option(
    "-s", "--nodes-label-selector", envvar="NODES_LABEL_SELECTOR", type=click.STRING,
    help="Label selector to filter nodes",
)
def run(
        kubernetes_conf_path,
        kubernetes_namespace,
        max_pod_creation_time,
        nodes_label_selector,
        create_new_namespace
):
    settings = Settings(kubernetes_namespace, max_pod_creation_time, nodes_label_selector)
    kuber = create_kuber(kubernetes_conf_path)

    kubernetes_namespace_instance = KuberNamespace(kuber, kubernetes_namespace)
    over_provisioning_pods_finder = LabeledPodsFinder(
        kuber, namespace=settings.kubernetes_namespace, label_selector=settings.nodes_label_selector
    )
    pods_creator = PodsCreator(kuber, settings.kubernetes_namespace)
    nodes_lister = NodesLister(kuber)

    test_runner = OverProvisioningTest(pods_creator, over_provisioning_pods_finder, nodes_lister)

    main(
        kubernetes_namespace_instance,
        create_new_namespace,
        test_runner,
        settings.max_pod_creation_time_in_seconds
    )


if __name__ == "__main__":
    run()
