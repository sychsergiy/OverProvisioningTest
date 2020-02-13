import click

from over_provisioning.main import main


@click.command()
@click.argument(
    "kubernetes_conf_path",
    envvar="KUBERNETES_CONF_PATH",
    type=click.Path(exists=True),
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
    help="Create new kubernetes namespace or use existent. "
    "By default create's new. In this namespace pods will be spawned",
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
    "--over-provisioning-pods-namespace",
    envvar="OVER_PROVISIONING_PODS_NAMESPACE",
    type=click.STRING,
    help="Namespace where over provisioning located",
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
    envvar="PODS_TO_CREATE_QUANTITY",
    type=click.INT,
    default=None,
    help="Quantity pods to create before finishing test. Created only for local running(to finish test)",
)
@click.option(
    "--local-development/--no-local-development",
    default=False,
    help="Define local or non local running mode to choose."
    " By default false. Options dependent on running mode: pod spec",
)
@click.option(
    "--max-amount-of-nodes",
    envvar="MAX_AMOUNT_OF_NODES",
    type=click.INT,
    help="Define max quantity of EC2 instances(nodes) which can be created",
)
@click.option(
    "--max-nodes-assigning-time",
    envvar="MAX_NODES_ASSIGNING_TIME",
    type=click.INT,
    help="Define max to wait on over provisioning pods will be assigned to new nodes",
)
def run(
    kubernetes_conf_path: str,
    kubernetes_namespace: str,
    max_pod_creation_time: float,
    over_provisioning_pods_label_selector: str,
    over_provisioning_pods_namespace: str,
    nodes_label_selector: str,
    create_new_namespace: bool,
    pods_to_create_quantity: int,
    local_development: bool,
    max_amount_of_nodes: int,
    max_nodes_assigning_time: int,
):
    main(
        kubernetes_conf_path,
        kubernetes_namespace,
        max_pod_creation_time,
        over_provisioning_pods_label_selector,
        over_provisioning_pods_namespace,
        nodes_label_selector,
        create_new_namespace,
        pods_to_create_quantity,
        local_development,
        max_amount_of_nodes,
        max_nodes_assigning_time,
    )


if __name__ == "__main__":
    run()
