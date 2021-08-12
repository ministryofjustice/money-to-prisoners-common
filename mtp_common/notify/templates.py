import functools

from django.utils.module_loading import autodiscover_modules


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
