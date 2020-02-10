from kubernetes import client

local_development_pod_spec = client.V1PodSpec(
    containers=[client.V1Container(name="test", image="nginx", )]
)

eks_development_pod_spec = client.V1PodSpec(
    scheduler_name="default-scheduler",
    priority=0,
    priority_class_name="default",
    node_selector={
        "kubernetes.io/role": "worker",
    },
    containers=[client.V1Container(
        resources={
            "limits": {"memory": "10737"},
            "requests": {"cpu": 0.2, "memory": "5368"},
        },
        name="test",
        image="nginx",
    )]
)
