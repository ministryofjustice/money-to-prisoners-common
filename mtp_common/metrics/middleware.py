import os
from time import perf_counter

from django.apps import apps
from prometheus_client import Histogram

request_duration = Histogram(
    'mtp_django_request_duration', 'Django HTTP request durations',
    labelnames=('view', 'method', 'status', 'pid'),
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 25.0, 50.0, float('inf'))
)
try:
    app = apps.get_app_config('metrics')
    app.register_collector(request_duration)
except LookupError:
    pass


class RequestMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.metrics_request_started = perf_counter()

        response = self.get_response(request)

        if hasattr(request, 'metrics_request_started'):
            view_name = getattr(getattr(request, 'resolver_match', None), 'view_name', None) or '<unnamed view>'
            duration = perf_counter() - request.metrics_request_started
            request_duration.labels(
                view=view_name,
                method=request.method,
                status=str(response.status_code),
                pid=str(os.getpid()),  # pid is needed as uwsgi runs with multiple workers
            ).observe(duration)

        return response
