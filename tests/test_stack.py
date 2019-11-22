import os
from unittest import mock

from kubernetes.client.configuration import Configuration
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException

from mtp_common.stack import StackInterrogationException, is_first_instance, get_current_pod
from tests.utils import SimpleTestCase


class StackTestCase(SimpleTestCase):
    def setup_k8s_responses(self, mock_config, mock_client, pod_name):
        os.environ['KUBERNETES_SERVICE_HOST'] = '127.0.0.1'
        os.environ['KUBERNETES_SERVICE_PORT'] = '9988'
        os.environ['POD_NAME'] = pod_name
        configuration = Configuration()
        configuration.host = 'http://127.0.0.1:9988'
        configuration.api_key = {'authorization': 'bearer T0ken'}
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

    @mock.patch('mtp_common.stack.client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_first_in_k8s(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-123')
        self.assertTrue(is_first_instance())
        args, kwargs = mock_client.CoreV1Api().list_namespaced_pod.call_args
        self.assertEqual(kwargs['namespace'], 'money-to-prisoners-test')
        self.assertEqual(kwargs['label_selector'], 'app=common')

    @mock.patch('mtp_common.stack.client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_not_first_in_k8s(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-234')
        self.assertFalse(is_first_instance())

    @mock.patch('mtp_common.stack.client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_not_first_in_k8s_because_terminating(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-345')
        self.assertFalse(is_first_instance())

    @mock.patch('mtp_common.stack.client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_not_in_k8s(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-123')
        mock_config.side_effect = ConfigException()
        with self.assertRaises(StackInterrogationException):
            is_first_instance()
        mock_client.assert_not_called()

    @mock.patch('mtp_common.stack.client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_forbidden_in_k8s(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-123')
        mock_client.CoreV1Api().list_namespaced_pod.side_effect = ApiException(status=403)
        with self.assertRaises(StackInterrogationException):
            is_first_instance()

    @mock.patch('mtp_common.stack.client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_get_current_pod(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-123')
        pod = get_current_pod()
        self.assertEqual(pod.status.phase, 'Running')

    @mock.patch('mtp_common.stack.client')
    @mock.patch('mtp_common.stack.load_incluster_config')
    def test_not_found_current_pod(self, mock_config, mock_client):
        self.setup_k8s_responses(mock_config, mock_client, pod_name='api-456')
        pod = get_current_pod()
        self.assertIsNone(pod)
