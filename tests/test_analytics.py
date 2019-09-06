from unittest import mock, TestCase

from mtp_common.analytics import genericised_pageview


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
