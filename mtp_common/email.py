from email.utils import parseaddr
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.template import loader
from django.utils.encoding import force_text


def send_email(to, text_template, subject, context=None,
               html_template=None, from_address=None):
    if not from_address:
        from_address = getattr(settings, 'MAILGUN_FROM_ADDRESS', '') or settings.DEFAULT_FROM_EMAIL
    if not isinstance(to, (list, tuple)):
        to = [to]
    template_context = {'static_url': urljoin(settings.SITE_URL, settings.STATIC_URL)}
    if context:
        template_context.update(context)

    text_body = loader.get_template(text_template).render(template_context)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body.strip('\n'),
        from_email=from_address,
        to=to
    )
    if html_template:
        html_body = loader.get_template(html_template).render(template_context)
        email.attach_alternative(html_body, 'text/html')

    if settings.ENVIRONMENT != 'prod':
        def is_test_email(address):
            try:
                address = parseaddr(force_text(address))[1]
                return any(
                    address.endswith(domain)
                    for domain in ('@local', '@mtp.local', '@outside.local')
                )
            except ValueError:
                pass

        if all(is_test_email(recipient) for recipient in email.recipients()):
            ConsoleEmailBackend(fail_silently=False).write_message(email)
            return

    email.send()
