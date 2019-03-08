import os
from unittest import mock

from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException
import responses

from mtp_common.stack import InstanceNotInAsgException, StackInterrogationException, is_first_instance
from tests.utils import SimpleTestCase


class StackTestCase(SimpleTestCase):
    def setup_aws_responses(self, rsps, mock_boto3, instance_id, asg_name):
        os.environ.pop('KUBERNETES_SERVICE_HOST', None)
        rsps.add(rsps.GET, 'http://169.254.169.254/latest/dynamic/instance-identity/document',
                 json={'instanceId': instance_id, 'region': 'eu-west-1'})
        mock_autoscaling_client = mock_boto3.client()
        autoscaling_instances = []
        if asg_name:
            autoscaling_instances.append({'AutoScalingGroupName': asg_name})
        mock_autoscaling_client.describe_auto_scaling_instances.return_value = {
            'AutoScalingInstances': autoscaling_instances
        }
        mock_autoscaling_client.describe_auto_scaling_groups.return_value = {
            'AutoScalingGroups': [{'Instances': [
                {'InstanceId': 'i-91234567890123456', 'LifecycleState': 'InService'},  # not first
                {'InstanceId': 'i-01234567890123456', 'LifecycleState': 'InService'},  # first
                {'InstanceId': 'i-00234567890123456', 'LifecycleState': 'Terminating'},  # not counted
            ]}]
        }

    @mock.patch('mtp_common.stack.boto3')
    def test_first_in_asg(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_aws_responses(rsps, mock_boto3, 'i-01234567890123456', 'test-asg')
            self.assertTrue(is_first_instance())

    @mock.patch('mtp_common.stack.boto3')
    def test_not_first_in_asg(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_aws_responses(rsps, mock_boto3, 'i-91234567890123456', 'test-asg')
            self.assertFalse(is_first_instance())

    @mock.patch('mtp_common.stack.boto3')
    def test_not_first_in_asg_because_terminating(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_aws_responses(rsps, mock_boto3, 'i-00234567890123456', 'test-asg')
            self.assertFalse(is_first_instance())

    @mock.patch('mtp_common.stack.boto3')
    def test_not_in_asg(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_aws_responses(rsps, mock_boto3, 'i-00004567890123456', None)
            with self.assertRaises(InstanceNotInAsgException):
                is_first_instance()

    @mock.patch('mtp_common.stack.boto3')
    def test_not_in_aws(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, 'http://169.254.169.254/latest/dynamic/instance-identity/document',
                     status=404)
            mock_autoscaling_client = mock_boto3.client()
            with self.assertRaises(StackInterrogationException):
                is_first_instance()
        mock_autoscaling_client.assert_not_called()

    def setup_k8s_responses(self, mock_config, mock_client, pod_name):
        from kubernetes.client.configuration import Configuration

        os.environ['KUBERNETES_SERVICE_HOST'] = '127.0.0.1'
        os.environ['KUBERNETES_SERVICE_PORT'] = '9988'
        os.environ['POD_NAME'] = pod_name
        configuration = Configuration()
        configuration.host = 'http://127.0.0.1:9988'
        Configuration.set_default(configuration)
        mock_config.return_value = None
        pod1 = mock.MagicMock()
        pod1.metadata.name = 'api-123'
        pod1.status.phase = 'Running'
        pod2 = mock.MagicMock()
        pod2.metadata.name = 'api-234'
        pod2.status.phase = 'Running'
        pod3 = mock.MagicMock()
        pod3.metadata.name = 'api-345'
        pod3.status.phase = 'Terminating'
        mock_client.CoreV1Api().list_namespaced_pod().items = [pod1, pod2, pod3]

    @mock.patch('mtp_common.stack.k8s_client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_first_in_k8s(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-123')
        self.assertTrue(is_first_instance())
        args, kwargs = mock_client.CoreV1Api().list_namespaced_pod.call_args
        self.assertEqual(kwargs['namespace'], 'money-to-prisoners-test')
        self.assertEqual(kwargs['label_selector'], 'app=common')

    @mock.patch('mtp_common.stack.k8s_client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_not_first_in_k8s(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-234')
        self.assertFalse(is_first_instance())

    @mock.patch('mtp_common.stack.k8s_client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_not_first_in_k8s_because_terminating(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-345')
        self.assertFalse(is_first_instance())

    @mock.patch('mtp_common.stack.k8s_client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_not_in_k8s(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-123')
        mock_config.side_effect = ConfigException()
        with self.assertRaises(StackInterrogationException):
            is_first_instance()
        mock_client.assert_not_called()

    @mock.patch('mtp_common.stack.k8s_client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_forbidden_in_k8s(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-123')
        mock_client.CoreV1Api().list_namespaced_pod.side_effect = ApiException(status=403)
        with self.assertRaises(StackInterrogationException):
            is_first_instance()
