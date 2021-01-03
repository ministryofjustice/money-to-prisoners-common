from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
import responses

from mtp_common.auth import urljoin, MojAnonymousUser
from mtp_common.auth.test_utils import generate_tokens
from mtp_common.test_utils import silence_logger
from tests.utils import SimpleTestCase


class NotificationTestCase(SimpleTestCase):
    def unauthenticated_request(self):
        return mock.MagicMock(
            user=MojAnonymousUser()
        )

    def authenticated_request(self):
        return mock.MagicMock(
            user=mock.MagicMock(
                token=generate_tokens()
            )
        )

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_unauthenticated_user_access(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'notifications'),
                json={'count': 1, 'results': [{
                    'target': 'target', 'level': 'warning',
                    'headline': 'Test', 'message': 'Body',
                    'start': '2017-11-29T12:00:00Z', 'end': None,
                }]},
            )
            response = self.load_mocked_template(
                """
                {% load mtp_common %}
                {% notification_banners request 'target' %}
                """,
                {'request': self.unauthenticated_request()},
            )
        response_content = response.content.decode(response.charset).strip()
        self.assertIn('Test', response_content)

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_authenticated_user_access(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'notifications'),
                json={'count': 1, 'results': [{
                    'target': 'target', 'level': 'warning',
                    'headline': 'Test', 'message': 'Body',
                    'start': '2017-11-29T12:00:00Z', 'end': None,
                }]},
            )
            response = self.load_mocked_template(
                """
                {% load mtp_common %}
                {% notification_banners request 'target' %}
                """,
                {'request': self.authenticated_request()},
            )
        response_content = response.content.decode(response.charset).strip()
        self.assertIn('Test', response_content)

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_api_errors_do_not_appear_on_page(self):
        with responses.RequestsMock() as rsps, silence_logger():
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'notifications'),
                body='error', status=500,
            )
            response = self.load_mocked_template(
                """
                {% load mtp_common %}
                {% notification_banners request 'target' %}
                """,
                {'request': self.authenticated_request()},
            )
        response_content = response.content.decode(response.charset).strip()
        self.assertEqual(response_content, '')

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_can_cascade_to_fallback_notification_targets(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'notifications') + '?target__startswith=target1',
                match_querystring=True,
                json={'count': 0, 'results': []},
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'notifications') + '?target__startswith=target2',
                match_querystring=True,
                json={'count': 1, 'results': [{
                    'target': 'target2', 'level': 'warning',
                    'headline': 'Test', 'message': 'Body',
                    'start': '2017-11-29T12:00:00Z', 'end': None,
                }]},
            )
            response = self.load_mocked_template(
                """
                {% load mtp_common %}
                {% notification_banners request 'target1' 'target2' %}
                """,
                {'request': self.authenticated_request()},
            )
        response_content = response.content.decode(response.charset).strip()
        self.assertIn('Test', response_content)

    def test_notifications_with_cache(self):
        cache.clear()
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'notifications'),
                json={'count': 1, 'results': [{
                    'target': 'target', 'level': 'warning',
                    'headline': 'Test', 'message': 'Body',
                    'start': '2017-11-29T12:00:00Z', 'end': None,
                }]},
            )
            self.load_mocked_template(
                """
                {% load mtp_common %}
                {% notification_banners request 'target' %}
                """,
                {'request': self.authenticated_request()},
            )
            response = self.load_mocked_template(
                """
                {% load mtp_common %}
                {% notification_banners request 'target' %}
                """,
                {'request': self.authenticated_request()},
            )
        response_content = response.content.decode(response.charset).strip()
        self.assertIn('Test', response_content)

    def test_notifications_without_cache(self):
        cache.clear()
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'notifications'),
                json={'count': 1, 'results': [{
                    'target': 'target', 'level': 'warning',
                    'headline': 'Test', 'message': 'Body',
                    'start': '2017-11-29T12:00:00Z', 'end': None,
                }]},
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'notifications'),
                json={'count': 1, 'results': [{
                    'target': 'target', 'level': 'warning',
                    'headline': 'Test', 'message': 'Body',
                    'start': '2017-11-29T12:00:00Z', 'end': None,
                }]},
            )
            self.load_mocked_template(
                """
                {% load mtp_common %}
                {% notification_banners request 'target' use_cache=False %}
                """,
                {'request': self.authenticated_request()},
            )
            response = self.load_mocked_template(
                """
                {% load mtp_common %}
                {% notification_banners request 'target' use_cache=False %}
                """,
                {'request': self.authenticated_request()},
            )
        response_content = response.content.decode(response.charset).strip()
        self.assertIn('Test', response_content)
