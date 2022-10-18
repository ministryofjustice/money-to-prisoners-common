import functools
import io
import logging
import typing

from django.conf import settings
from notifications_python_client import NotificationsAPIClient, prepare_upload

logger = logging.getLogger('mtp')


class TemplateError(Exception):
    pass


class NotifyClient:
    @classmethod
    @functools.lru_cache
    def shared_client(cls):
        return cls()

    def __init__(self):
        """
        Ensures GOV.UK Notify account exists and populates a map of template names to IDs
        :raises TemplateError if templates with duplicate names exist or if the generic one is missing
        """
        self._template_map = {}
        self.client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

        self.reply_to_public = getattr(settings, 'GOVUK_NOTIFY_REPLY_TO_PUBLIC', None)
        self.reply_to_staff = getattr(settings, 'GOVUK_NOTIFY_REPLY_TO_STAFF', None)
        is_staff_app = getattr(settings, 'MOJ_INTERNAL_SITE', False)
        self.reply_to_default = self.reply_to_staff if is_staff_app else self.reply_to_public

        templates = self.client.get_all_templates(template_type='email')
        duplicates = set()
        for template in templates['templates']:
            if template['name'] in self._template_map:
                duplicates.add(template['name'])
            if template['name'] == 'generic':
                if '((subject))' not in template['subject']:
                    raise TemplateError('Email template ‘generic’ is missing `((subject))` subject personalisation')
                if '((message))' not in template['body']:
                    raise TemplateError('Email template ‘generic’ is missing `((message))` body personalisation')
            self._template_map[template['name']] = template['id']
        if duplicates:
            # if duplicates are found, apps cannot reliably choose appropriate template
            raise TemplateError(f'Duplicate email template names found in GOV.UK Notify: {sorted(duplicates)}')
        if 'generic' not in self._template_map:
            raise TemplateError('Email template ‘generic’ not found')

    def get_template_id_for_name(self, template_name: str) -> str:
        """
        Maps a template name (as used in code) to an ID from GOV.UK Notify
        :raises TemplateError if no template is found
        """
        try:
            return self._template_map[template_name]
        except KeyError:
            raise TemplateError(f'Email template ‘{template_name}’ not found')

    @classmethod
    def can_send_email_to_address(cls, email_address: str) -> bool:
        """
        Returns False for email addresses whose domain name is configured to be ignored in non-production
        This is useful in order to prevent fake email addresses leading to error responses from GOV.UK Notify
        """
        if settings.ENVIRONMENT != 'prod':
            email_domain = email_address.split('@', 1)[1]
            if email_domain.lower() in getattr(settings, 'GOVUK_NOTIFY_BLOCKED_DOMAINS', ()):
                return False
        return True

    def send_email(
        self,
        template_name: str,
        to: typing.Union[str, typing.List[str]],
        personalisation: dict = None,
        reference: str = None,
        staff_email: bool = None,
    ) -> typing.List[typing.Optional[str]]:
        """
        Sends a templated email via GOV.UK Notify with personalisations
        :returns list of GOV.UK Notify message IDs
        :raises TemplateError if template is not found
        :raises notifications_python_client.errors.APIError if email cannot be sent
        """
        template_id = self.get_template_id_for_name(template_name)
        if isinstance(to, str):
            to = [to]
        if staff_email is True:
            reply_to = self.reply_to_staff
        elif staff_email is False:
            reply_to = self.reply_to_public
        else:
            reply_to = self.reply_to_default
        if personalisation:
            prepared_files = {}
            for field, content in personalisation.items():
                if isinstance(content, bytes):
                    prepared_files[field] = prepare_upload(
                        io.BytesIO(content),
                        confirm_email_before_download=False,
                        retention_period='52 weeks',
                    )
                elif isinstance(content, (io.RawIOBase, io.BufferedIOBase)):
                    prepared_files[field] = prepare_upload(
                        content,
                        confirm_email_before_download=False,
                        retention_period='52 weeks',
                    )
            personalisation.update(prepared_files)
        message_ids = []
        for email_address in to:
            if not self.can_send_email_to_address(email_address):
                logger.warning(
                    f'Skipping sending {template_name} template email to {email_address} because domain is ignored'
                )
                message_ids.append(None)
                continue
            response = self.client.send_email_notification(
                email_address=email_address,
                template_id=template_id,
                personalisation=personalisation,
                reference=reference,
                email_reply_to_id=reply_to,
            )
            message_id = response.get('id')
            message_ids.append(message_id)
            if not message_id or response.get('reference') != reference:
                logger.exception(
                    f'Problem sending {template_name} template email (ID: {message_id}) with reference `{reference}`'
                )
        return message_ids

    def send_plain_text_email(
        self,
        to: typing.Union[str, typing.List[str]],
        subject: str,
        message: str,
        reference: str = None,
        staff_email: bool = None,
    ) -> typing.List[str]:
        """
        Send plain text email using the generic template with no control over formatting/links
        This should only be used as a last resort or exceptional fallback
        """
        return self.send_email(
            template_name='generic',
            to=to,
            personalisation={
                'subject': subject,
                'message': message,
            },
            reference=reference,
            staff_email=staff_email,
        )
