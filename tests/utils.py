from unittest import mock

from django.test import SimpleTestCase as DjangoSimpleTestCase
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from mtp_common.analytics import AnalyticsPolicy


class SimpleTestCase(DjangoSimpleTestCase):
    @mock.patch('tests.urls.mocked_context')
    @mock.patch('tests.urls.mocked_template')
    def load_mocked_template(self, template, context, mocked_template, mocked_context, **extra):
        mocked_template.return_value = template
        mocked_context.return_value = context
        return self.client.get(reverse('dummy'), **extra)


class TestAcceptingCookiePolicyMiddleware(MiddlewareMixin):
    """
    Used in tests that mimic a user clicking accept on a cookie prompt
    """

    def process_response(self, request, response):
        AnalyticsPolicy(request).set_cookie_policy(response, True)
        return response
