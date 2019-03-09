from django.apps import apps
from django.http import HttpResponse, Http404


def metrics_view(request):
    try:
        from prometheus_client import exposition
    except ImportError:
        raise Http404()

    app = apps.get_app_config('metrics')
    encoder, content_type = exposition.choose_encoder(request.META.get('HTTP_ACCEPT'))
    content = encoder(app.metric_registry)
    return HttpResponse(content, content_type=content_type)
