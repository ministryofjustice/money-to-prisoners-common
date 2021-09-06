import base64
import io
import typing
from urllib.parse import urlencode, urljoin

import boto3
from django.conf import settings
from django.http.response import StreamingHttpResponse
from django.utils.crypto import get_random_string
from kubernetes import client as k8s_client
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException, load_incluster_config


class S3BucketError(Exception):
    pass


class S3BucketClient:
    """
    Utility to access S3 bucket shared between MTP apps within one environment
    The primary use is to store files generated asynchronously for later download, e.g. via a link in an email
    """

    def __init__(self):
        # load config from inside k8s cluster
        try:
            load_incluster_config()
        except ConfigException as e:
            raise S3BucketError('Not running inside Kubernetes cluster', e)

        # load k8s secret from app's namespace which contains S3 bucket name and associated IAM access token
        try:
            secret = k8s_client.CoreV1Api().read_namespaced_secret(
                name='s3',
                namespace=f'money-to-prisoners-{settings.ENVIRONMENT}',
            )
            self.s3_secret = {
                key: base64.b64decode(value).decode()
                for key, value in secret.data.items()
            }
        except ApiException as e:
            raise S3BucketError('S3 secret not found', e)

        # check contents
        if any(
            key not in self.s3_secret
            for key in ('access_key_id', 'secret_access_key', 'bucket_name')
        ):
            raise S3BucketError('S3 secret is missing required keys')

        # create authenticated connection to S3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.s3_secret['access_key_id'],
            aws_secret_access_key=self.s3_secret['secret_access_key'],
        )

    def upload(
        self,
        file_contents: typing.Union[bytes, io.RawIOBase, io.BufferedIOBase],
        path: str,
        content_type: str = None,
        tags: dict = None,
    ):
        if isinstance(file_contents, bytes):
            file_contents = io.BytesIO(file_contents)
        tags = dict(tags or {}, app=settings.APP, environment=settings.ENVIRONMENT)
        extra_args = {'Tagging': urlencode(tags)}
        if content_type:
            extra_args['ContentType'] = content_type
        self.s3_client.upload_fileobj(
            Fileobj=file_contents,
            Bucket=self.s3_secret['bucket_name'],
            Key=path,
            ExtraArgs=extra_args,
        )

    def dowload(self, path: str) -> bytes:
        file_contents = io.BytesIO()
        self.s3_client.download_fileobj(
            Bucket=self.s3_secret['bucket_name'],
            Key=path,
            Fileobj=file_contents,
        )
        return file_contents.getvalue()

    def download_as_streaming_response(self, path: str) -> StreamingHttpResponse:
        s3_object = self.s3_client.get_object(
            Bucket=self.s3_secret['bucket_name'],
            Key=path,
        )
        response = StreamingHttpResponse(
            streaming_content=s3_object['Body'],
            content_type=s3_object['ContentType'],
        )
        response['Last-Modified'] = s3_object['ResponseMetadata']['HTTPHeaders']['last-modified']
        return response


def make_bucket_download_url(path_prefix: str, filename: str) -> dict:
    """
    Given a path prefix and file name, generates a longer path to store objects in S3
    in order to make bucket paths not guessable/enumerable.
    The download url links directly to the mtp-emails app.
    """
    if not path_prefix or not filename:
        raise ValueError
    path_prefix = path_prefix.strip('/') + '/' + get_random_string(35)
    bucket_path = f'{path_prefix}/{filename}'
    return {
        'bucket_path': bucket_path,
        'download_url': urljoin(settings.EMAILS_URL, f'/download/{bucket_path}'),
    }
