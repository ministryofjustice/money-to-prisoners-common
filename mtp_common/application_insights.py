from django.conf import settings
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter


def tagging_processor(envelope):
    """
    Sets common tags for Azure Application Insights
    """
    envelope.tags['ai.cloud.location'] = settings.ENVIRONMENT
    envelope.tags['ai.cloud.role'] = f'mtp-{settings.APP}'
    envelope.tags['ai.application.ver'] = settings.APP_BUILD_TAG
    return True


class AppInsightsLogHandler(AzureLogHandler):
    """
    Django logging handler for Azure Application Insights
    """

    def __init__(self, **options):
        super().__init__(**options)
        super().add_telemetry_processor(tagging_processor)


class AppInsightsTraceExporter(AzureExporter):
    """
    Trace exporter for Azure Application Insights
    """

    def __init__(self, **options):
        super().__init__(**options)
        self.add_telemetry_processor(tagging_processor)
