import io
import os
from unittest import mock
from urllib.parse import parse_qsl

from django.test import override_settings
from kubernetes.client.rest import ApiException
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME

from mtp_common.s3_bucket import S3BucketClient, S3BucketError, make_download_token, parse_download_token
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
                {'app': 'common', 'environment': 'test'},
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
            tags.pop('app')
            tags.pop('environment')
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
            response = client.download_stream('test.csv')
            header_bytes = bytes(response)
            body_bytes = b''.join(iter(response))
            self.assertEqual(mock_s3_client.get_object.call_count, 1)
            kwargs = mock_s3_client.get_object.call_args_list[0].kwargs
            self.assertEqual(kwargs['Bucket'], 'cloud-platform-TEST1')
            self.assertEqual(kwargs['Key'], 'test.csv')
            self.assertIn(b'text/csv', header_bytes)
            self.assertIn(b'01 Sep 2021 12:00:00', header_bytes)
            self.assertEqual(body_bytes.decode(), '1,2,3\n')


@override_settings(S3_BUCKET_SIGNING_KEY='0000111122223333')
class DownloadTokenTestCase(SimpleTestCase):
    def test_token_round_trip(self):
        tokens = make_download_token('backup/2021-09-02', 'files.zip')
        self.assertNotEqual(tokens['bucket_path'], 'backup/2021-09-02/files.zip',
                            msg='full bucket path should have some random characters added')
        self.assertGreater(len(tokens['download_token']), len(tokens['bucket_path']),
                           msg='download token should contain a signature')
        bucket_path = parse_download_token(tokens['download_token'])
        self.assertEqual(bucket_path, tokens['bucket_path'],
                         msg='parsed download token should be the full bucket path')
        path_prefix, _random, _signature, filename = tokens['download_token'].rsplit('/', 3)
        self.assertEqual(path_prefix, 'backup/2021-09-02',
                         msg='path prefix should be preserved in download token')
        self.assertEqual(filename, 'files.zip',
                         msg='trailing file name should be preserved in download token')

    def test_token_tampering(self):
        download_token = make_download_token('export', '2021-09.zip')['download_token']
        path_prefix, random, signature, filename = download_token.split('/')
        parse_download_token(f'{path_prefix}/{random}/{signature}/{filename}')  # proves that full token still parses
        with self.assertRaises(ValueError, msg='modified path prefix still parsed'):
            parse_download_token(f'downloads/{random}/{signature}/{filename}')
        with self.assertRaises(ValueError, msg='modified random prefix still parsed'):
            parse_download_token(f'{path_prefix}/0000000000000/{signature}/{filename}')
        with self.assertRaises(ValueError, msg='invalid signature still parsed'):
            parse_download_token(f'{path_prefix}/{random}/123abc000/{filename}')
        with self.assertRaises(ValueError, msg='modified filename still parsed'):
            parse_download_token(f'{path_prefix}/{random}/{signature}/2021-08.zip')

    def test_invalid_tokens(self):
        for token in ('', 'export/2021-09.zip', 'export/0000000000000/2021-09.zip'):
            with self.assertRaises(ValueError):
                parse_download_token(token)
