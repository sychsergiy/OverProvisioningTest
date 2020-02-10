from kubernetes import client


class KuberNamespace:
    def __init__(self, kuber: client.CoreV1Api, name: str):
        self._kuber = kuber
        self._name = name

    def create(self):
        return self._kuber.create_namespace(
            client.V1Namespace(metadata=client.V1ObjectMeta(name=self._name))
        )

    def delete(self):
        return self._kuber.delete_namespace(self._name)

    def check_if_exists(self):
        try:
            self._kuber.read_namespace(self._name)
        except client.rest.ApiException as e:
            if e.status == 404:
                raise RuntimeError(f"Provided namespace: {self._name} doesnt exists.")
            else:
                raise e
        return True
