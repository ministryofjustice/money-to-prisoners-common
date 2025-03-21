from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import gettext_lazy as _

from mtp_common.forms import replace_default_error_messages


class AppConfig(DjangoAppConfig):
    name = 'mtp_common'
    verbose_name = _('Prisoner money')

    def ready(self):
        replace_default_error_messages()
