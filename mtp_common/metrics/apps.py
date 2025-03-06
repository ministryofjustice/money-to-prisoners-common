from django.apps import AppConfig as DjangoAppConfig
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import gettext_lazy as _
from prometheus_client.registry import CollectorRegistry


class AppConfig(DjangoAppConfig):
    name = 'mtp_common.metrics'
    verbose_name = _('Prisoner money metrics')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metric_registry = CollectorRegistry()

    def ready(self):
        super().ready()
        autodiscover_modules('metrics')

    def register_collector(self, collector):
        self.metric_registry.register(collector)
