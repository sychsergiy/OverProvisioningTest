from kubernetes import client


class NodesFinder:
    def __init__(self, kuber: client.CoreV1Api, label_selector: str):
        self._kuber = kuber
        self._label_selector = label_selector

    def find_by_label_selector(self):
        """
        label_selector variations:
          only label key: "label_key"
          label key with value: "label_key=label_value"
          list of mixed labels: "label_key,label_key_2=label_value"
        """
        nodes = self._kuber.list_node(label_selector=self._label_selector)
        return nodes.items

    def find_all(self):
        nodes = self._kuber.list_node()
        return nodes.items
