import functools
import logging
import typing

from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient

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
        :raises TemplateError if templates with duplicate names exist
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
            self._template_map[template['name']] = template['id']
        if duplicates:
            # if duplicates are found, apps cannot reliably choose appropriate template
            raise TemplateError(f'Duplicate email template names found in GOV.UK Notify: {sorted(duplicates)}')

    def get_template_id_for_name(self, template_name: str) -> str:
        """
        Maps a template name (as used in code) to an ID from GOV.UK Notify
        :raises TemplateError if no template is found
        """
        try:
            return self._template_map[template_name]
        except KeyError:
            raise TemplateError(f'Email template ‘{template_name}’ not found')

    def send_email(
        self,
        template_name: str,
        to: typing.Union[str, typing.List[str]],
        personalisation: dict = None,
        reference: str = None,
        staff_email: bool = None,
    ) -> typing.List[str]:
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
        message_ids = []
        for email_address in to:
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
                logging.exception(
                    f'Problem sending {template_name} template email (ID: {message_id}) with reference `{reference}`'
                )
        return message_ids
