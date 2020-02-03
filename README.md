# Over Provisioning Test

To install dependencies:
```bash
pip install -r requirements.txt
```

Use `python cli.py --help` command to see docs
```
$ python cli.py --help
Usage: cli.py [OPTIONS] KUBERNETES_CONF_PATH

Options:
  -n, --kubernetes-namespace TEXT
                                  Namespace where over provisioning test will
                                  be executed
  --create-new-namespace / --no-create-new-namespace
                                  Create new kubernetes namespace. If not set,
                                  test will try to find existent. By default
                                  True
  -t, --max-pod-creation-time FLOAT
                                  Max time for pod creation in seconds. If pod
                                  creation hit this limit test will fail
  -s, --nodes-label-selector TEXT
                                  Label selector to filter nodes
  -p, --pods-to-create-quantity INTEGER
                                  Quantity pods to create before finishing
                                  test. Created only for local running(to
                                  finish test)
  --help                          Show this message and exit.

```

Example of usage with full command options:
```bash
python cli.py kube_config.yaml \
    --kubernetes-namespace=test-ns-0  \
    --max-pod-creation-time=60 \
    --over-provisioning-pods-label-selector=test_over_prov_pods_label_selector \
    --nodes-label-selector=over_prov_pod  \
    --no-create-new-namespace
```
Example of usage with full command options shortcuts:
```bash
python cli.py kube_config.yaml \
    -n test-ns-0 -t 60 -l test_over_prov_pods_label_selector \
    -s over_prov_pod --create-new-namespace
```

All options also can be passed with environment variables(uppercased and underscores instead of dashes).
Usage with env vars:
```bash
export KUBERNETES_CONF_PATH="kube_config.yaml"
export KUBERNETES_NAMESPACE="test-ns"
export MAX_POD_CREATION_TIME_IN_SECONDS=60
export OVER_PROVISIONING_PODS_LABEL_SELECTOR="test_over_prov_pods_label_selector"
export NODES_LABEL_SELECTOR="test_nodes_selector"

python cli.py --no-create-new-namespace
```

When you are running test locally using minikube use `--pods-to-create-quantity`
 option to limit quantity of created pods.
 

