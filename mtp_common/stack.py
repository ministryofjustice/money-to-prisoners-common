import os

from django.conf import settings
from kubernetes import client as k8s_client
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException, load_incluster_config


class StackException(Exception):
    pass


class StackInterrogationException(StackException):
    pass


def is_first_instance(current_pod_name=None):
    """
    Returns True if the current pod is the first replica in cloud platform cluster
    """
    current_pod_name = current_pod_name or os.environ.get('POD_NAME')
    if not current_pod_name:
        raise StackInterrogationException('Pod name not known')

    namespace = 'money-to-prisoners-%s' % settings.ENVIRONMENT
    try:
        load_incluster_config()
    except ConfigException as e:
        raise StackInterrogationException(e)
    try:
        response = k8s_client.CoreV1Api().list_namespaced_pod(
            namespace=namespace,
            label_selector='app=%s' % settings.APP,
            watch=False,
        )
    except ApiException as e:
        raise StackInterrogationException(e)
    pod_names = sorted(pod.metadata.name for pod in filter(lambda pod: pod.status.phase == 'Running', response.items))
    return bool(pod_names and pod_names[0] == current_pod_name)
