from unittest import mock

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponseForbidden
from django.test import SimpleTestCase


class CsrfTestCase(SimpleTestCase):
    login_url = reverse_lazy('login')

    def setUp(self):
        self.mocked_api_client = mock.patch('mtp_common.auth.backends.api_client')
        mocked_api_client = self.mocked_api_client.start()
        mocked_api_client.authenticate.return_value = {
            'pk': 1,
            'token': 'abc',
            'user_data': {'first_name': 'First', 'last_name': 'Last',
                          'username': 'test'}
        }

        self.client = self.client_class(enforce_csrf_checks=True)

    def tearDown(self):
        self.mocked_api_client.stop()

    def assertInvalidCsrfResponse(self, response):  # noqa
        self.assertEqual(response.status_code, 403)
        messages = '\n'.join(str(message) for message in response.context['messages'])
        self.assertIn('Please try again', messages)

    def assertValidCsrfResponse(self, response):  # noqa
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.has_header('location'))

    def test_missing_csrf_cookie(self):
        response = self.client.post(self.login_url, data={
            'username': 'test',
            'password': '1234',
        })
        self.assertInvalidCsrfResponse(response)

    def test_invalid_csrf_token(self):
        self.client.get(self.login_url)
        response = self.client.post(self.login_url, data={
            'username': 'test',
            'password': '1234',
            'csrfmiddlewaretoken': 'invalid',
        })
        self.assertInvalidCsrfResponse(response)

    @mock.patch('tests.utils.get_template_source')
    def test_successful_csrf_challenge(self, mocked_template):
        mocked_template.return_value = '{% csrf_token %}'
        self.client.get(self.login_url)
        csrf_token = self.client.cookies[settings.CSRF_COOKIE_NAME]
        response = self.client.post(self.login_url, data={
            'username': 'test',
            'password': '1234',
            'csrfmiddlewaretoken': csrf_token.value,
        })
        self.assertValidCsrfResponse(response)

    @mock.patch('django.views.csrf.csrf_failure')
    def test_turning_off_csrf_failure_override(self, mocked_csrf_failure):
        from mtp_common.auth.csrf import default_csrf_behaviour
        from mtp_common.auth.views import login

        default_csrf_behaviour(login)
        mocked_csrf_failure.return_value = HttpResponseForbidden(b'Django CSRF response')
        response = self.client.post(self.login_url, data={
            'username': 'test',
            'password': '1234',
        })
        self.assertTrue(mocked_csrf_failure.called)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, b'Django CSRF response')
        login.no_moj_csrf = False
