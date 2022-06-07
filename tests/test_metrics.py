import re
from unittest import mock

from django.test import override_settings
from django.urls import reverse

from tests.utils import SimpleTestCase


@mock.patch('mtp_common.auth.basic._check_basic_auth', lambda *args: True)
@override_settings(METRICS_USER='???', METRICS_PASS='???')
class MetricsTestCase(SimpleTestCase):
    def test_app_info_metrics(self):
        response = self.client.get(reverse('prometheus_metrics'))
        content = response.content.decode()
        matches = re.search('^mtp_app_info{([^}]+)}', content, flags=re.MULTILINE)
        app_info = matches.group(1)
        self.assertIn('app="common"', app_info)
        self.assertIn('environment="test"', app_info)

    def test_request_duration_metrics(self):
        self.client.get(reverse('dummy'))  # ensure dummy view was called at least once
        response = self.client.get(reverse('prometheus_metrics'))
        content = response.content.decode()
        self.assertTrue(any(
            'view="dummy"' in line
            for line in content.splitlines()
            if line.startswith('mtp_django_request_duration_count')
        ))
