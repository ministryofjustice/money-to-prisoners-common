import io
import os
from unittest import mock

from kubernetes.client.rest import ApiException
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME

from mtp_common.s3_bucket import S3BucketClient, S3BucketError
from tests.utils import SimpleTestCase


def mock_s3_secret_response(mock_client, valid_response=True):
    secret = mock.MagicMock()
    if valid_response:
        data = {
            'bucket_arn': 'YXJuOmF3czpzMzo6OmNsb3VkLXBsYXRmb3JtLVRFU1Qx', 'bucket_name': 'Y2xvdWQtcGxhdGZvcm0tVEVTVDE=',
            'access_key_id': 'QUtJQTAwMDAwMDAwMDA=', 'secret_access_key': 'MDAwMDAwMDAwMDAwMDAwMDAwMDA=',
        }
    else:
        data = {}
    secret.data = data
    mock_client.CoreV1Api().read_namespaced_secret.return_value = secret


class S3BucketTestCase(SimpleTestCase):
    @mock.patch.dict(os.environ, {SERVICE_HOST_ENV_NAME: ''})
    def test_outside_cluster(self):
        with self.assertRaises(S3BucketError) as e:
            S3BucketClient()
        self.assertIn('Not running inside Kubernetes cluster', str(e.exception))

    @mock.patch('mtp_common.s3_bucket.k8s_client')
    @mock.patch('mtp_common.s3_bucket.load_incluster_config')
    def test_cannot_find_secret(self, mock_config, mock_client):
        self.setup_k8s_incluster_config(mock_config, pod_name='app')
        mock_client.CoreV1Api().read_namespaced_secret.side_effect = ApiException(status=404)
        with self.assertRaises(S3BucketError) as e:
            S3BucketClient()
        self.assertIn('S3 secret not found', str(e.exception))

    @mock.patch('mtp_common.s3_bucket.k8s_client')
    @mock.patch('mtp_common.s3_bucket.load_incluster_config')
    def test_malformed_secret(self, mock_config, mock_client):
        self.setup_k8s_incluster_config(mock_config, pod_name='app')
        mock_s3_secret_response(mock_client, valid_response=False)
        with self.assertRaises(S3BucketError) as e:
            S3BucketClient()
        self.assertIn('S3 secret is missing required keys', str(e.exception))

    @mock.patch('mtp_common.s3_bucket.k8s_client')
    @mock.patch('mtp_common.s3_bucket.load_incluster_config')
    def test_upload_passes_params_to_boto(self, mock_config, mock_client):
        self.setup_k8s_incluster_config(mock_config, pod_name='app')
        mock_s3_secret_response(mock_client)
        client = S3BucketClient()
        with mock.patch.object(client, 's3_client') as mock_s3_client:
            client.upload(b'00000', 'test.bin')
            self.assertEqual(mock_s3_client.upload_fileobj.call_count, 1)
            kwargs = mock_s3_client.upload_fileobj.call_args_list[0].kwargs
            self.assertEqual(kwargs['Bucket'], 'cloud-platform-TEST1')
            self.assertEqual(kwargs['Key'], 'test.bin')
            self.assertTrue(isinstance(kwargs['Fileobj'], io.BytesIO))

    @mock.patch('mtp_common.s3_bucket.k8s_client')
    @mock.patch('mtp_common.s3_bucket.load_incluster_config')
    def test_download_passes_params_to_boto(self, mock_config, mock_client):
        self.setup_k8s_incluster_config(mock_config, pod_name='app')
        mock_s3_secret_response(mock_client)
        client = S3BucketClient()
        with mock.patch.object(client, 's3_client') as mock_s3_client:
            mock_s3_client.download_fileobj.side_effect = lambda **kw: kw['Fileobj'].write(b'12345')
            data = client.dowload('test.bin')
            self.assertEqual(mock_s3_client.download_fileobj.call_count, 1)
            kwargs = mock_s3_client.download_fileobj.call_args_list[0].kwargs
            self.assertEqual(data, b'12345')
            self.assertEqual(kwargs['Bucket'], 'cloud-platform-TEST1')
            self.assertEqual(kwargs['Key'], 'test.bin')
