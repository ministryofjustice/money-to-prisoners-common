import io
import os
from unittest import mock
from urllib.parse import parse_qsl

from django.test import override_settings
from kubernetes.client.rest import ApiException
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME

from mtp_common.s3_bucket import S3BucketClient, S3BucketError, generate_upload_path, get_download_url
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
            self.assertDictEqual(
                dict(parse_qsl(kwargs['ExtraArgs']['Tagging'])),
                {'application': 'common', 'environment-name': 'test'},
            )
            self.assertNotIn('ContentType', kwargs['ExtraArgs'])
            self.assertTrue(isinstance(kwargs['Fileobj'], io.BytesIO))

    @mock.patch('mtp_common.s3_bucket.k8s_client')
    @mock.patch('mtp_common.s3_bucket.load_incluster_config')
    def test_upload_passes_extra_tags_to_boto(self, mock_config, mock_client):
        self.setup_k8s_incluster_config(mock_config, pod_name='app')
        mock_s3_secret_response(mock_client)
        client = S3BucketClient()
        with mock.patch.object(client, 's3_client') as mock_s3_client:
            client.upload('1,2,3\n'.encode(), 'test.csv', tags={'abc': '123', 'key': 'value'})
            self.assertEqual(mock_s3_client.upload_fileobj.call_count, 1)
            kwargs = mock_s3_client.upload_fileobj.call_args_list[0].kwargs
            tags = dict(parse_qsl(kwargs['ExtraArgs']['Tagging']))
            tags.pop('application')
            tags.pop('environment-name')
            self.assertDictEqual(tags, {'abc': '123', 'key': 'value'})

    @mock.patch('mtp_common.s3_bucket.k8s_client')
    @mock.patch('mtp_common.s3_bucket.load_incluster_config')
    def test_upload_passes_content_type_to_boto(self, mock_config, mock_client):
        self.setup_k8s_incluster_config(mock_config, pod_name='app')
        mock_s3_secret_response(mock_client)
        client = S3BucketClient()
        with mock.patch.object(client, 's3_client') as mock_s3_client:
            client.upload('1,2,3\n'.encode(), 'test.csv', content_type='text/csv')
            self.assertEqual(mock_s3_client.upload_fileobj.call_count, 1)
            kwargs = mock_s3_client.upload_fileobj.call_args_list[0].kwargs
            self.assertEqual(kwargs['ExtraArgs']['ContentType'], 'text/csv')

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

    @mock.patch('mtp_common.s3_bucket.k8s_client')
    @mock.patch('mtp_common.s3_bucket.load_incluster_config')
    def test_streaming_download(self, mock_config, mock_client):
        self.setup_k8s_incluster_config(mock_config, pod_name='app')
        mock_s3_secret_response(mock_client)
        client = S3BucketClient()
        with mock.patch.object(client, 's3_client') as mock_s3_client:
            mock_s3_client.get_object.return_value = {
                # NB: this is a small subset of what's returned by S3
                'ResponseMetadata': {'HTTPHeaders': {'last-modified': 'Wed, 01 Sep 2021 12:00:00 GMT'}},
                'Body': io.BytesIO('1,2,3\n'.encode()),
                'ContentType': 'text/csv',
            }
            response = client.download_as_streaming_response('test.csv')
            header_bytes = bytes(response)
            body_bytes = b''.join(iter(response))
            self.assertEqual(mock_s3_client.get_object.call_count, 1)
            kwargs = mock_s3_client.get_object.call_args_list[0].kwargs
            self.assertEqual(kwargs['Bucket'], 'cloud-platform-TEST1')
            self.assertEqual(kwargs['Key'], 'test.csv')
            self.assertIn(b'text/csv', header_bytes)
            self.assertIn(b'01 Sep 2021 12:00:00', header_bytes)
            self.assertEqual(body_bytes.decode(), '1,2,3\n')


@override_settings(EMAILS_URL='http://localhost:8006')
class S3BucketDownloadURLTestCase(SimpleTestCase):
    def test_make_upload_path_and_download_url(self):
        bucket_path = generate_upload_path('emails/2021', '09-06.zip')
        self.assertTrue(bucket_path.startswith('emails/2021'),
                        msg='bucket path should preserve folder structure')
        self.assertTrue(bucket_path.endswith('/09-06.zip'),
                        msg='bucket path should preserve filename')
        self.assertGreater(len(bucket_path), len('emails/2021') + len('/09-06.zip'),
                           msg='bucket path should have added randomness')
        download_url = get_download_url(bucket_path)
        self.assertTrue(download_url.startswith('http://localhost:8006/'))
        self.assertTrue(download_url.endswith(bucket_path))

    def test_cannot_make_upload_path_with_empty_inputs(self):
        with self.assertRaises(ValueError):
            generate_upload_path('', 'filename.csv')
        with self.assertRaises(ValueError):
            generate_upload_path('/', 'filename.csv')
        with self.assertRaises(ValueError):
            generate_upload_path('folder/abc/', '')

    def test_cannot_get_download_url_outside_of_emails_folder(self):
        samples = (
            '',
            'names.csv',
            'backup/names.csv',
        )
        for sample in samples:
            with self.assertRaises(ValueError):
                get_download_url(sample)
