import base64

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.urls import reverse

from tests.utils import SimpleTestCase
from mtp_common.test_utils import silence_logger


class BasicAuthTestCase(SimpleTestCase):
    def test_unconfigured(self):
        with self.assertRaises(ImproperlyConfigured), silence_logger('django.request'):
            self.client.get(reverse('basic-auth'))

    @override_settings(BASIC_USER='user', BASIC_PASSWORD='pword')
    def test_unauthorised_access(self):
        response = self.client.get(reverse('basic-auth'))
        self.assertContains(response, 'Authentication required', status_code=401)

    @override_settings(BASIC_USER='user', BASIC_PASSWORD='pword')
    def test_authorised_access(self):
        auth = f'Basic {base64.b64encode("user:pword".encode()).decode()}'
        response = self.client.get(reverse('basic-auth'), HTTP_AUTHORIZATION=auth)
        self.assertContains(response, 'DUMMY', status_code=200)
