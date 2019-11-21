from django.apps import apps
from django.http import HttpResponse
from prometheus_client import exposition

from mtp_common.auth.basic import basic_auth


@basic_auth('METRICS_USER', 'METRICS_PASS')
def metrics_view(request):
    app = apps.get_app_config('metrics')
    encoder, content_type = exposition.choose_encoder(request.META.get('HTTP_ACCEPT'))
    content = encoder(app.metric_registry)
    return HttpResponse(content, content_type=content_type)
