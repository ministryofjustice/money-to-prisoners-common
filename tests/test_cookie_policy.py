from unittest import mock

from mtp_common.utils import CookiePolicy
from tests.utils import SimpleTestCase


class CookiePolicyTestCase(SimpleTestCase):
    def test_default_cookie_policies(self):
        request = mock.MagicMock(
            COOKIES={}
        )
        cookie_policy = CookiePolicy(request)
        self.assertEqual(cookie_policy.usage, True)
        with self.assertRaises(AttributeError):
            print(cookie_policy.settings)

        cookie_policy = CookiePolicy(request, settings=False)
        self.assertEqual(cookie_policy.usage, True)
        self.assertEqual(cookie_policy.settings, False)

    def test_stored_cookie_policies(self):
        request = mock.MagicMock(
            COOKIES={'cookie_policy': '{"usage":false}'}
        )
        cookie_policy = CookiePolicy(request)
        self.assertEqual(cookie_policy.usage, False)

        request = mock.MagicMock(
            COOKIES={'cookie_policy': '{"settings":false}'}
        )
        cookie_policy = CookiePolicy(request, settings=True)
        self.assertEqual(cookie_policy.usage, True)
        self.assertEqual(cookie_policy.settings, False)

        request = mock.MagicMock(
            COOKIES={'cookie_policy': '{"usage":false, "settings":false}'}
        )
        cookie_policy = CookiePolicy(request)
        self.assertEqual(cookie_policy.usage, False)
        with self.assertRaises(AttributeError):
            print(cookie_policy.settings)

    def test_invalid_cookie_policies(self):
        invalid_cookies = ['', '{}', '123', '""', '[]', '{"usage":}']
        for invalid_cookie in invalid_cookies:
            request = mock.MagicMock(
                COOKIES={'cookie_policy': invalid_cookie}
            )
            cookie_policy = CookiePolicy(request)
            self.assertEqual(cookie_policy.usage, True)
