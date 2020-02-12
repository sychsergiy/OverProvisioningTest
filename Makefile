help:
	@echo "Please use \`make <target>' where <target> is one of"

local_run:
	python cli.py kube_config.yaml \
      --kubernetes-namespace=test-ns-0  \
      --max-pod-creation-time=60 \
      --over-provisioning-pods-label-selector="test_over_prov_pods_label_selector" \
      --over-provisioning-pods-namespace="over-prov-pods" \
      --nodes-label-selector="over_prov_pod"  \
      --create-new-namespace \
      --pods-to-create-quantity=3 \
      --max-amount-of-nodes=15 \
      --local-development

run:
	python cli.py kube_remote_config.yaml \
      --kubernetes-namespace=test-ns-0  \
      --max-pod-creation-time=60 \
      --over-provisioning-pods-label-selector="app.kubernetes.io/name=cluster-overprovisioner" \
      --over-provisioning-pods-namespace="jhub" \
      --nodes-label-selector="kubernetes.io/role=worker"  \
      --max-amount-of-nodes=4 \
      --create-new-namespace \
