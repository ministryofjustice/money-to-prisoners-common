import functools
import typing

from django.utils.module_loading import autodiscover_modules

from mtp_common.notify import NotifyClient, TemplateError


class NotifyTemplateRegistry:
    """
    Base class for registering templates that are expected to exist in GOV.UK Notify
    """
    _registry = {}

    def __init_subclass__(cls):
        templates = getattr(cls, 'templates', None)
        if not isinstance(templates, dict):
            raise AttributeError('Subclasses of NotifyTemplateRegistry must define a "templates" dict')
        for template_name, template_details in templates.items():
            if template_name in cls._registry:
                raise KeyError(f'Notify template {template_name} is already registered, but names must be unique')
            cls._registry[template_name] = template_details

    @classmethod
    @functools.lru_cache
    def get_all_templates(cls):
        autodiscover_modules('notify.templates', register_to=cls)
        return cls._registry

    @classmethod
    def check_notify_templates(cls) -> (bool, typing.List[str]):
        """
        Checks that templates exist in GOV.UK Notify and whether their contents are as expected.
        If a template is missing or does not include an expected personalisation, it's considered to be an error.
        If a template's subject of body does not match what's expected, it's considered a warning.
        :returns (bool, [str]) with the boolean flag indicating a hard error and a list of warning/error messages
        """
        client = NotifyClient.shared_client()
        notify_templates = client.client.get_all_templates(template_type='email')
        notify_templates = {
            notify_template['id']: notify_template
            for notify_template in notify_templates['templates']
        }

        error = False
        messages = []
        for template_name, template_details in cls.get_all_templates().items():
            try:
                template_id = client.get_template_id_for_name(template_name)
                notify_template = notify_templates[template_id]
            except (TemplateError, KeyError):
                error = True
                messages.append(f'Email template ‘{template_name}’ not found')
                continue

            # check subject
            if (
                template_details['subject'].strip() !=
                notify_template['subject'].strip()
            ):
                messages.append(f'Email template ‘{template_name}’ has different subject')

            # check body
            if (
                template_details['body'].strip() !=
                notify_template['body'].strip()
            ):
                messages.append(f'Email template ‘{template_name}’ has different body copy')

            # check personalisation
            notify_template_personalisation = set(notify_template.get('personalisation', {}))
            expected_personalisation = set(template_details['personalisation'])
            missing_personalisation = expected_personalisation.difference(notify_template_personalisation)
            if missing_personalisation:
                error = True
                missing = ', '.join(missing_personalisation)
                messages.append(f'Email template ‘{template_name}’ is missing required personalisation: {missing}')

        return error, messages


class CommonNotifyTemplates(NotifyTemplateRegistry):
    """
    Templates that mtp-common expects to exist in GOV.UK Notify
    """
    templates = {
        # this template is used as a fallback to send plain text messages with a generic subject
        'generic': {
            'subject': 'Prisoner money',
            'body': '((message))',
            'personalisation': ['message'],
        },
    }
