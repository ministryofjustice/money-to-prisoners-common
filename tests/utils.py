import os
from unittest import mock

from django.test import SimpleTestCase as DjangoSimpleTestCase
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from kubernetes.client.configuration import Configuration

from mtp_common.analytics import AnalyticsPolicy


class SimpleTestCase(DjangoSimpleTestCase):
    @mock.patch('tests.urls.mocked_context')
    @mock.patch('tests.urls.mocked_template')
    def load_mocked_template(self, template, context, mocked_template, mocked_context, **extra):
        mocked_template.return_value = template
        mocked_context.return_value = context
        return self.client.get(reverse('dummy'), **extra)

    @classmethod
    def setup_k8s_incluster_config(cls, mock_config, pod_name):
        os.environ['KUBERNETES_SERVICE_HOST'] = '127.0.0.1'
        os.environ['KUBERNETES_SERVICE_PORT'] = '9988'
        os.environ['POD_NAME'] = pod_name
        configuration = Configuration()
        configuration.host = 'http://127.0.0.1:9988'
        configuration.api_key = {'authorization': 'bearer T0ken'}
        Configuration.set_default(configuration)
        mock_config.return_value = None


class TestAcceptingCookiePolicyMiddleware(MiddlewareMixin):
    """
    Used in tests that mimic a user clicking accept on a cookie prompt
    """

    def process_response(self, request, response):
        AnalyticsPolicy(request).set_cookie_policy(response, True)
        return response
