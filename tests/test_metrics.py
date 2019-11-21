from unittest import mock

from django.test import RequestFactory, override_settings

from mtp_common.metrics.views import metrics_view
from tests.utils import SimpleTestCase


@mock.patch('mtp_common.auth.basic._check_basic_auth', lambda *args: True)
@override_settings(METRICS_USER='???', METRICS_PASS='???')
class MetricsTestCase(SimpleTestCase):
    def test_app_info_metrics(self):
        request = RequestFactory().get('/metrics/')
        response = metrics_view(request)
        self.assertContains(response, 'app="common"')
        self.assertContains(response, 'environment="test"')
