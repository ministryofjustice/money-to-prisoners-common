import os

from django.conf import settings
from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException, load_incluster_config


class StackException(Exception):
    pass


class StackInterrogationException(StackException):
    pass


def get_pod_list(app=None):
    try:
        load_incluster_config()
    except ConfigException as e:
        raise StackInterrogationException(e)

    filters = {
        'namespace': f'money-to-prisoners-{settings.ENVIRONMENT}',
    }
    if app:
        filters['label_selector'] = f'app={app}'
    try:
        api = client.CoreV1Api()
        return api.list_namespaced_pod(watch=False, **filters)
    except ApiException as e:
        raise StackInterrogationException(e)


def is_first_instance():
    """
    Returns True if the current pod is the first replica in cloud platform cluster
    """
    current_pod_name = os.environ.get('POD_NAME')
    if not current_pod_name:
        raise StackInterrogationException('Pod name not known')
    pod_list = get_pod_list(app=settings.APP)
    pod_names = sorted(
        pod.metadata.name
        for pod in filter(lambda pod: pod.status.phase == 'Running', pod_list.items)
    )
    return bool(pod_names and pod_names[0] == current_pod_name)


def get_current_pod():
    """
    Get current pod details
    Returns None unlike `is_first_instance` if not running within Cloud Platform
    """
    current_pod_name = os.environ.get('POD_NAME')
    if not current_pod_name:
        return None
    pod_list = get_pod_list(app=settings.APP)
    return next(filter(lambda pod: pod.metadata.name == current_pod_name, pod_list.items), None)
