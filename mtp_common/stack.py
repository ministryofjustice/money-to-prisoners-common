import os

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from kubernetes import client as k8s_client
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException, load_incluster_config
import requests


class StackException(Exception):
    pass


class StackInterrogationException(StackException):
    pass


class InstanceNotInAsgException(StackException):
    pass


def is_first_instance():
    """
    Returns True if application is "first". Used to run commands only once in load-balanced environments.
    """
    if os.environ.get('KUBERNETES_SERVICE_HOST'):
        return is_first_instance_k8s()
    return is_first_instance_aws()


def is_first_instance_aws():
    """
    Returns True if the current instance is the first instance in the ASG group,
    sorted by instance_id.
    """
    try:
        # get instance id and aws region
        instance_details = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document',
                                        timeout=5).json()
        instance_id = instance_details['instanceId']
        instance_region = instance_details['region']
    except (requests.RequestException, ValueError, KeyError) as e:
        raise StackInterrogationException(e)

    try:
        # get instance's autoscaling group
        autoscaling_client = boto3.client('autoscaling', region_name=instance_region)
        response = autoscaling_client.describe_auto_scaling_instances(InstanceIds=[instance_id])
        assert len(response['AutoScalingInstances']) == 1
        autoscaling_group = response['AutoScalingInstances'][0]['AutoScalingGroupName']
    except ClientError as e:
        raise StackInterrogationException(e)
    except AssertionError:
        raise InstanceNotInAsgException()

    try:
        # list in-service instances in autoscaling group
        # instances being launched or terminated should not be considered
        response = autoscaling_client.describe_auto_scaling_groups(AutoScalingGroupNames=[autoscaling_group])
        assert len(response['AutoScalingGroups']) == 1
        autoscaling_group_instance_ids = sorted(
            instance['InstanceId']
            for instance in response['AutoScalingGroups'][0]['Instances']
            if instance['LifecycleState'] == 'InService'
        )
    except (ClientError, AssertionError) as e:
        raise StackInterrogationException(e)

    return bool(autoscaling_group_instance_ids and autoscaling_group_instance_ids[0] == instance_id)


def is_first_instance_k8s(current_pod_name=None):
    """
    Returns True if the current pod is the first replica in Kubernetes cluster.
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
