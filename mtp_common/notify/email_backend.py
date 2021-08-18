import logging
import typing

from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage

from mtp_common.notify import NotifyClient

logger = logging.getLogger('mtp')


class NotifyEmailBackend(BaseEmailBackend):
    """
    Email backend that uses NotifyClient to send plain text emails.
    Should only be used as a fallback because attachments, links and formatting are not supported.
    MTP apps should use the `send_email` task instead with this backend handling emails for core Django functionality.
    """

    def send_messages(self, email_messages: typing.List[EmailMessage]):
        for email_message in email_messages:
            to = email_message.to + email_message.cc + email_message.bcc
            subject = email_message.subject
            message = email_message.body
            if email_message.attachments:
                logger.error(
                    f'Sending email ‘{subject}’ using GOV.UK Notify but discarding attachments! '
                    f'Avoid using {self.__class__.__name__}, it should only exist as a fallback.'
                )
            else:
                logger.warning(
                    f'Sending email ‘{subject}’ using GOV.UK Notify. '
                    f'Avoid using {self.__class__.__name__}, it should only exist as a fallback.'
                )
            NotifyClient.shared_client().send_plain_text_email(
                to=to,
                subject=subject,
                message=message,
            )
        return len(email_messages)
