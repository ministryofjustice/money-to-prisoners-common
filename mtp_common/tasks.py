from email.utils import parseaddr
import logging
import smtplib
from urllib.parse import urljoin

try:
    from anymail.exceptions import AnymailRequestsAPIError
    from anymail.message import AnymailMessage
except ImportError:
    AnymailRequestsAPIError = None
    AnymailMessage = None
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.template import loader
from django.utils.encoding import force_text

from mtp_common.spooling import Context, spoolable

logger = logging.getLogger('mtp')
if AnymailRequestsAPIError:
    mail_errors = (AnymailRequestsAPIError,)
else:
    mail_errors = (smtplib.SMTPException,)
mail_class = AnymailMessage if AnymailMessage else EmailMultiAlternatives


@spoolable()
def send_email(to, text_template, subject, context=None, html_template=None, from_address=None,
               anymail_tags=(), retry_attempts=2, spoolable_ctx: Context = None):
    default_from_address = getattr(settings, 'MAILGUN_FROM_ADDRESS', '') or settings.DEFAULT_FROM_EMAIL
    from_address = from_address or default_from_address
    if not isinstance(to, (list, tuple)):
        to = [to]
    if hasattr(settings, 'PUBLIC_STATIC_URL'):
        static_url = settings.PUBLIC_STATIC_URL
    else:
        static_url = urljoin(settings.SITE_URL, settings.STATIC_URL)
    template_context = {
        'static_url': static_url,
        **(context or {})
    }

    email = prepare_email(from_address, to, subject, text_template, html_template, template_context, anymail_tags)

    if settings.ENVIRONMENT != 'prod':
        if all(is_test_email(recipient) for recipient in email.recipients()):
            ConsoleEmailBackend(fail_silently=False).write_message(email)
            return

    try:
        email.send()
    except mail_errors as e:
        if hasattr(e, 'status_code') and e.status_code == 400:
            try:
                message = e.response.json()['message']
            except (AttributeError, TypeError, ValueError, KeyError):
                message = 'Mailgun 400 response'
            if "'to' parameter is not a valid address" in message:
                logger.warning(message)
            else:
                logger.exception(message)
            return
        if not spoolable_ctx.spooled or not retry_attempts:
            raise
        send_email(to, text_template, subject, context=context,
                   html_template=html_template, from_address=from_address,
                   anymail_tags=anymail_tags,
                   retry_attempts=retry_attempts - 1)


def prepare_email(from_address, to, subject, text_template, html_template, template_context, anymail_tags):
    text_body = loader.get_template(text_template).render(template_context)
    email = mail_class(
        subject=subject,
        body=text_body.strip('\n'),
        from_email=from_address,
        to=to
    )
    if anymail_tags and isinstance(email, AnymailMessage):
        email.tags = list(map(force_text, anymail_tags))
    if html_template:
        html_body = loader.get_template(html_template).render(template_context)
        email.attach_alternative(html_body, 'text/html')
    return email


def is_test_email(address):
    try:
        address = parseaddr(force_text(address))[1]
        return any(
            address.endswith(domain)
            for domain in ('@local', '.local')
        )
    except ValueError:
        pass
