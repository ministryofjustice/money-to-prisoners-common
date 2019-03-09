import warnings

from django.http import Http404
from django.test import RequestFactory

from mtp_common.metrics.views import metrics_view
from tests.utils import SimpleTestCase


class MetricsTestCase(SimpleTestCase):
    def test_app_info_metrics(self):
        request = RequestFactory().get('/metrics/')
        try:
            import prometheus_client  # noqa: F401
            response = metrics_view(request)
            self.assertContains(response, 'app="common"')
            self.assertContains(response, 'environment="test"')
        except ImportError:
            warnings.warn('prometheus_client not installed')
            with self.assertRaises(Http404):
                metrics_view(request)
