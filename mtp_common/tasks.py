import logging
import typing

from notifications_python_client.errors import APIError, InvalidResponse

from mtp_common.notify import NotifyClient
from mtp_common.s3_bucket import S3BucketClient
from mtp_common.spooling import Context, spoolable

logger = logging.getLogger('mtp')


@spoolable(body_params=('personalisation',))
def send_email(
    template_name: str,
    to: typing.Union[str, typing.List[str]],
    personalisation: dict = None,
    reference: str = None,
    staff_email: bool = None,
    retry_attempts: int = 2,
    spoolable_ctx: Context = None,
):
    """
    Asynchronously sends an email using GOV.UK Notify.
    A temporary error or connection problem allows the spooler to retry twice by default.
    If a template is missing, the spooler will not retry.
    """
    client = NotifyClient.shared_client()
    try:
        client.send_email(
            template_name=template_name,
            to=to,
            personalisation=personalisation,
            reference=reference,
            staff_email=staff_email,
        )
    except APIError as e:
        should_retry = (
            # no retry without uWSGI spooler
            spoolable_ctx.spooled
            # no retry if run out of retry attempts
            and retry_attempts
            # retry only for "service unavailable" / "internal error" statuses
            and 500 <= e.status_code < 600
            # …unless it was caused by an invalid json response
            and not isinstance(e, InvalidResponse)
        )
        if should_retry:
            send_email(
                template_name=template_name,
                to=to,
                personalisation=personalisation,
                reference=reference,
                staff_email=staff_email,
                retry_attempts=retry_attempts - 1,
            )
        else:
            raise e


@spoolable(body_params=('file_contents',))
def upload_to_s3(file_contents: bytes, path: str, content_type: str = None, tags: dict = None):
    """
    Asynchronously uploads a file into shared S3 bucket
    """
    client = S3BucketClient()
    client.upload(
        file_contents=file_contents,
        path=path,
        content_type=content_type,
        tags=tags,
    )
