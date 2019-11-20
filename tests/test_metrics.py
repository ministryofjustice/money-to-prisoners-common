from django.test import RequestFactory

from mtp_common.metrics.views import metrics_view
from tests.utils import SimpleTestCase


class MetricsTestCase(SimpleTestCase):
    def test_app_info_metrics(self):
        request = RequestFactory().get('/metrics/')
        response = metrics_view(request)
        self.assertContains(response, 'app="common"')
        self.assertContains(response, 'environment="test"')
