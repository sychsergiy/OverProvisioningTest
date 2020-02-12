## Over Provisioning Test

Spawning pods with until all `over provisioning`
 pods change their nodes(which mean tests passed).

### To install dependencies:
```bash
pip install -r requirements.txt
```

### Running
During running important events will logged.
After running `report.json` file will be created with test results info.
Test can exit with two statuses: 
0 - means test passed,
1 - means test failed or error occurs

###
Use `python cli.py --help` command to see docs
```
$ python cli.py --help
Usage: cli.py [OPTIONS] KUBERNETES_CONF_PATH

Options:
  -n, --kubernetes-namespace TEXT
                                  Namespace where over provisioning test will
                                  be executed
  --create-new-namespace / --no-create-new-namespace
                                  Create new kubernetes namespace or use
                                  existent. By default create's new. In this
                                  namespace pods will be spawned
  -t, --max-pod-creation-time FLOAT
                                  Max time for pod creation in seconds. If pod
                                  creation hit this limit test will fail
  -l, --over-provisioning-pods-namespace TEXT
                                  Namespace where over provisioning located
  -l, --over-provisioning-pods-label-selector TEXT
                                  Set label selector to find over provisioning
                                  pods
  -s, --nodes-label-selector TEXT
                                  Label selector to filter nodes
  -p, --pods-to-create-quantity INTEGER
                                  Quantity pods to create before finishing
                                  test. Created only for local running(to
                                  finish test)
  --local-development / --no-local-development
                                  Define local or non local running mode to
                                  choose. By default false. Options dependent
                                  on running mode: pod spec.
  --max-amount-of-nodes INTEGER   Define max quantity of EC2 instances(nodes)
                                  which can be created
  --help                          Show this message and exit.
```

Example of usage with full command options:
```bash
python cli.py {KUBERNETES_CONF_PATH} \
      --kubernetes-namespace=test-ns-0  \
      --max-pod-creation-time=60 \
      --over-provisioning-pods-label-selector="app.kubernetes.io/name=cluster-overprovisioner" \
      --over-provisioning-pods-namespace="jhub" \
      --nodes-label-selector="kubernetes.io/role=worker"  \
      --max-amount-of-nodes=4 \
      --create-new-namespace \
```

All options also can be passed with environment variables(uppercased and underscores instead of dashes).
Usage with env vars:
```bash
export KUBERNETES_CONF_PATH="kube_config.yaml"
export KUBERNETES_NAMESPACE="test-ns-0"
export MAX_POD_CREATION_TIME_IN_SECONDS=60
export OVER_PROVISIONING_PODS_LABEL_SELECTOR="test_over_prov_pods_label_selector"
export OVER_PROVISIONING_PODS_NAMESPACE="jhub"
export NODES_LABEL_SELECTOR="test_nodes_selector"
export MAX_AMOUNT_OF_NODES=4

python cli.py --create-new-namespace
```

When you are running test locally using minikube use `--pods-to-create-quantity`
 option to limit quantity of created pods and
 `--local-development` to use specific pod spec for local development.
 

