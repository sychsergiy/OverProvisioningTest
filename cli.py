import click

from main import main

from settings import Settings


@click.command()
@click.argument(
    "kubernetes_conf_path", envvar="KUBERNETES_CONF_PATH", type=click.Path(exists=True),
)
@click.option(
    "-n", "--kubernetes-namespace", envvar="KUBERNETES_NAMESPACE", type=click.STRING,
    help="Namespace where overprovisoning test will be executed"
)  # todo: create namespace or use existent
@click.option(
    "-t", "--max-pod-creation-time", envvar="MAX_POD_CREATION_TIME", type=click.FLOAT,
    help="Max time for pod creation in seconds. If pod creation hit this limit test will fail"
)
@click.option(
    "-s", "--nodes-label-selector", envvar="NODES_LABEL_SELECTOR", type=click.STRING,
    help="Label selector to filter nodes",
)
def run(kubernetes_conf_path, kubernetes_namespace, max_pod_creation_time, nodes_label_selector):
    settings = Settings(kubernetes_namespace, max_pod_creation_time, nodes_label_selector)
    main(settings, kubernetes_conf_path)


if __name__ == "__main__":
    run()
