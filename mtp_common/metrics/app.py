from django.apps import AppConfig as DjangoAppConfig
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import gettext_lazy as _


class AppConfig(DjangoAppConfig):
    name = 'mtp_common.metrics'
    verbose_name = _('Prisoner money metrics')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from prometheus_client.registry import CollectorRegistry

            self.metric_registry = CollectorRegistry()
        except ImportError:
            self.metric_registry = None

    def ready(self):
        super().ready()
        if self.metric_registry:
            autodiscover_modules('metrics')

    def register_collector(self, collector):
        if self.metric_registry:
            self.metric_registry.register(collector)
