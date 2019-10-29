import json
from unittest import mock, TestCase

from django.test import override_settings, modify_settings

from mtp_common.analytics import AnalyticsPolicy, genericised_pageview
from tests.utils import SimpleTestCase


@override_settings(GOOGLE_ANALYTICS_ID='ABC123')
class CookiePolicyTestCase(SimpleTestCase):
    template = """
    {% extends 'mtp_common/mtp_base.html' %}
    """

    def test_analytics_enabled_if_required_implicitly(self):
        # i.e. `ANALYTICS_REQUIRED` setting is missing, so assumed to be True
        response = self.load_mocked_template(self.template, {})
        self.assertContains(response, 'ABC123')

        response = self.load_mocked_template(
            self.template, {},
            HTTP_COOKIE=f'{AnalyticsPolicy.cookie_name}="{{\\"usage\\":true}}"',
        )
        self.assertContains(response, 'ABC123')

    @override_settings(ANALYTICS_REQUIRED=True)
    def test_analytics_enabled_if_required_explicity(self):
        self.test_analytics_enabled_if_required_implicitly()

    @override_settings(ANALYTICS_REQUIRED=False)
    def test_analytics_not_enabled_if_not_required(self):
        response = self.load_mocked_template(self.template, {})
        self.assertNotContains(response, 'ABC123')

    @override_settings(ANALYTICS_REQUIRED=False)
    def test_analytics_can_be_disabled_if_not_required(self):
        response = self.load_mocked_template(
            self.template, {},
            HTTP_COOKIE=f'{AnalyticsPolicy.cookie_name}="{{\\"usage\\":false}}"',
        )
        self.assertNotContains(response, 'ABC123')

    @override_settings(ANALYTICS_REQUIRED=False)
    def test_analytics_can_be_enabled_when_not_required(self):
        response = self.load_mocked_template(
            self.template, {},
            HTTP_COOKIE=f'{AnalyticsPolicy.cookie_name}="{{\\"usage\\":true}}"',
        )
        self.assertContains(response, 'ABC123')

    @override_settings(ANALYTICS_REQUIRED=False)
    def test_analytics_not_enabled_if_not_required_and_cookie_is_malformed(self):
        response = self.load_mocked_template(
            self.template, {},
            HTTP_COOKIE=f'{AnalyticsPolicy.cookie_name}="{{\\"usage\\":}}"',
        )
        self.assertNotContains(response, 'ABC123')

    def test_valid_cookie_policies(self):
        valid_cookies = ['{"usage":true}', '{"usage": true, "marketing": false}']
        for valid_cookie in valid_cookies:
            request = mock.MagicMock(
                COOKIES={AnalyticsPolicy.cookie_name: valid_cookie}
            )
            analytics_policy = AnalyticsPolicy(request)
            self.assertTrue(analytics_policy.is_cookie_policy_accepted(request))

    def test_invalid_cookie_policies(self):
        invalid_cookies = ['', '{}', '123', '""', '[]', '{"usage":}', '{"usage": "yes"}']
        for invalid_cookie in invalid_cookies:
            request = mock.MagicMock(
                COOKIES={AnalyticsPolicy.cookie_name: invalid_cookie}
            )
            analytics_policy = AnalyticsPolicy(request)
            self.assertFalse(analytics_policy.is_cookie_policy_accepted(request))

    @modify_settings(
        MIDDLEWARE={
            'append': 'tests.utils.TestAcceptingCookiePolicyMiddleware',
        },
    )
    def test_setting_cookie_policy(self):
        self.load_mocked_template(self.template, {})
        cookie = self.client.cookies[AnalyticsPolicy.cookie_name]
        self.assertDictEqual(json.loads(cookie.value), {'usage': True})


class GenericisedPageviewTestCase(TestCase):
    """
    Tests related to genericised_pageview.
    """

    def test_complete(self):
        """
        Test with complete set of data.
        """
        request = mock.MagicMock()
        request.build_absolute_uri.return_value = (
            'http://test/'
            '?utm_campaign=campaign_name'
            '&utm_medium=campain_medium'
            '&utm_source=campain_source'
        )
        request.path = '/test/'

        ga_data = genericised_pageview(request, title='My title')

        self.assertDictEqual(
            ga_data,
            {
                'page': '/test/',
                'location': 'http://test/',
                'title': 'My title',
                'campaignName': 'campaign_name',
                'campaignMedium': 'campain_medium',
                'campaignSource': 'campain_source',
            },
        )

    def test_minimal(self):
        """
        Test with minimal set of data.
        """
        request = mock.MagicMock()
        request.build_absolute_uri.return_value = '//test/'
        request.path = '/test/'

        ga_data = genericised_pageview(request)

        self.assertDictEqual(
            ga_data,
            {
                'page': '/test/',
                'location': 'https://test/',
                'title': None,
                'campaignName': None,
                'campaignMedium': None,
                'campaignSource': None,
            },
        )
