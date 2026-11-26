from django.conf import settings
from django.core import cache as django_cache
from django.test import SimpleTestCase, override_settings
from requests.exceptions import HTTPError
import responses

from mtp_common import prisoner_search
from mtp_common.auth import urljoin


def build_prisoner_search_url(path):
    return urljoin(settings.HMPPS_OFFENDER_SEARCH_BASE_URL, path, trailing_slash=False)


class BaseTestCase(SimpleTestCase):
    def setUp(self):
        django_cache.cache.clear()

    def _mock_successful_auth_request(self, rsps, token='my-token'):
        rsps.add(
            responses.POST,
            urljoin(
                settings.HMPPS_AUTH_BASE_URL,
                '/oauth/token?grant_type=client_credentials',
                trailing_slash=False,
            ),
            json={
                'access_token': token,
                'expires_in': 3600,
            },
            status=200,
        )


class CanAccessPrisonerSearchTestCase(SimpleTestCase):
    def test_can_access_when_configured(self):
        self.assertTrue(prisoner_search.can_access_prisoner_search())

    @override_settings(HMPPS_OFFENDER_SEARCH_BASE_URL='')
    def test_cannot_access_without_base_url(self):
        self.assertFalse(prisoner_search.can_access_prisoner_search())


class GetLocationTestCase(BaseTestCase):
    """
    Tests related to the get_location function.
    """

    def _get_location(self, mocked_response, status=200):
        with responses.RequestsMock() as rsps:
            self._mock_successful_auth_request(rsps)
            rsps.add(
                responses.GET,
                build_prisoner_search_url('/prisoner/A1401AE'),
                json=mocked_response,
                status=status,
            )
            location = prisoner_search.get_location('A1401AE')
            self.assertEqual(rsps.calls[-1].request.headers['Authorization'], 'Bearer my-token')
        return location

    def test_prisoner_in_prison(self):
        location = self._get_location({
            'prisonerNumber': 'A1401AE',
            'prisonId': 'BXI',
            'prisonName': 'Brixton (HMP)',
            'cellLocation': 'H-2-001',
            'status': 'ACTIVE IN',
        })
        self.assertEqual(location, {
            'nomis_id': 'BXI',
            'name': 'Brixton (HMP)',
            'cell_location': 'H-2-001',
        })

    def test_prisoner_without_cell_location(self):
        location = self._get_location({
            'prisonerNumber': 'A1401AE',
            'prisonId': 'BXI',
            'prisonName': 'Brixton (HMP)',
        })
        self.assertEqual(location, {'nomis_id': 'BXI', 'name': 'Brixton (HMP)'})

    def test_released_prisoner(self):
        location = self._get_location({
            'prisonerNumber': 'A1401AE',
            'prisonId': 'OUT',
            'prisonName': 'Outside',
            'status': 'INACTIVE OUT',
        })
        self.assertEqual(location, {'nomis_id': prisoner_search.RELEASED_PRISON_ID, 'name': 'Outside'})

    def test_prisoner_in_transfer(self):
        location = self._get_location({
            'prisonerNumber': 'A1401AE',
            'prisonId': 'TRN',
            'prisonName': 'Transfer',
            'status': 'INACTIVE TRN',
        })
        self.assertEqual(location, {'nomis_id': prisoner_search.IN_TRANSFER_PRISON_ID, 'name': 'Transfer'})

    def test_missing_prison_name_falls_back_to_code(self):
        location = self._get_location({'prisonerNumber': 'A1401AE', 'prisonId': 'BXI'})
        self.assertEqual(location, {'nomis_id': 'BXI', 'name': 'BXI'})

    def test_returns_none_without_prison(self):
        self.assertIsNone(self._get_location({'prisonerNumber': 'A1401AE'}))

    def test_unknown_prisoner_raises_http_error(self):
        with self.assertRaises(HTTPError) as e:
            self._get_location({'status': 404, 'userMessage': 'Not found'}, status=404)
        self.assertEqual(e.exception.response.status_code, 404)
