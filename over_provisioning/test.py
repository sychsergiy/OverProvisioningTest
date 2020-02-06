import logging
import sys

from kubernetes import client, config

from over_provisioning.tests.runner import OneOverProvisioningPodTest

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_kuber(config_file_path=None):
    config.load_kube_config(config_file_path)
    kuber = client.CoreV1Api()
    return kuber


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
