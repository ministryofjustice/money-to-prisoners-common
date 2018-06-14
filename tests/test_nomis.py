from django.conf import settings
from django.test import SimpleTestCase, override_settings
from requests.exceptions import ConnectionError
import responses

from mtp_common import nomis
from mtp_common.auth import urljoin
from mtp_common.auth.test_utils import generate_tokens
from mtp_common.test_utils import silence_logger


class NomisApiTestCase(SimpleTestCase):
    @override_settings(NOMIS_API_CLIENT_TOKEN='abc.abc.abc')
    def test_client_token_taken_from_settings(self):
        self.assertEqual(nomis.get_client_token(), settings.NOMIS_API_CLIENT_TOKEN)
        self.assertTrue(nomis.can_access_nomis())

    @override_settings(NOMIS_API_CLIENT_TOKEN='',
                       TOKEN_RETRIEVAL_USERNAME='token-user',
                       TOKEN_RETRIEVAL_PASSWORD='abc')
    def test_client_token_cached_from_api(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, 'http://localhost:8000/oauth2/token/', json=generate_tokens())
            rsps.add(rsps.GET, 'http://localhost:8000/tokens/nomis/', json={
                'token': '1234567890',
                'expires': None,
            })
            rsps.add(rsps.POST, 'http://localhost:8000/oauth2/revoke_token/')
            self.assertTrue(nomis.can_access_nomis())
        self.assertEqual(nomis.get_client_token(), '1234567890')

    @override_settings(NOMIS_API_CLIENT_TOKEN='',
                       TOKEN_RETRIEVAL_USERNAME='token-user',
                       TOKEN_RETRIEVAL_PASSWORD='abc')
    def test_cannot_access_nomis_without_token(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, 'http://localhost:8000/oauth2/token/', json=generate_tokens())
            rsps.add(rsps.GET, 'http://localhost:8000/tokens/nomis/', status=404)
            rsps.add(rsps.POST, 'http://localhost:8000/oauth2/revoke_token/')
            with silence_logger():
                self.assertFalse(nomis.can_access_nomis())

    def test_get_account_balances(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                urljoin(settings.NOMIS_API_BASE_URL, '/prison/BMI/offenders/A1471AE/accounts/'),
                json={
                    'cash': 500,
                    'savings': 0,
                    'spends': 25,
                },
                status=200,
            )

            balances = nomis.get_account_balances('BMI', 'A1471AE')
            self.assertEqual(balances, {'cash': 500, 'savings': 0, 'spends': 25})

    def test_retry_on_connection_error(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                urljoin(settings.NOMIS_API_BASE_URL, '/prison/BMI/offenders/A1471AE/accounts/'),
                body=ConnectionError()
            )
            rsps.add(
                responses.GET,
                urljoin(settings.NOMIS_API_BASE_URL, '/prison/BMI/offenders/A1471AE/accounts/'),
                json={
                    'cash': 500,
                    'savings': 0,
                    'spends': 25,
                },
                status=200,
            )

            balances = nomis.get_account_balances('BMI', 'A1471AE', retries=1)
            self.assertEqual(balances, {'cash': 500, 'savings': 0, 'spends': 25})

    def assertHousingFormatStructure(self, nomis_response, expected_dict):  # noqa: N802
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                urljoin(settings.NOMIS_API_BASE_URL, '/offenders/A1401AE/location/'),
                json=nomis_response
            )
            location = nomis.get_location('A1401AE')
        self.assertEqual(location, expected_dict)

    def test_housing_location_no_housing(self):
        self.assertHousingFormatStructure(
            {
                'establishment': {
                    'code': 'BXI',
                    'desc': 'BRIXTON (HMP)'
                }
            },
            {'nomis_id': 'BXI', 'name': 'BRIXTON (HMP)'}
        )

    def test_housing_location_string_housing(self):
        self.assertHousingFormatStructure(
            {
                'establishment': {
                    'code': 'BXI',
                    'desc': 'BRIXTON (HMP)'
                },
                'housing_location': 'BXI-H-2-001'
            },
            {
                'nomis_id': 'BXI',
                'name': 'BRIXTON (HMP)',
                'housing_location': {
                    'description': 'BXI-H-2-001',
                    'levels': [
                        {'type': 'Wing', 'value': 'H'},
                        {'type': 'Landing', 'value': '2'},
                        {'type': 'Cell', 'value': '001'},
                    ]
                }
            }
        )

    def test_housing_location_dict_housing(self):
        self.assertHousingFormatStructure(
            {
                'establishment': {
                    'code': 'BXI',
                    'desc': 'BRIXTON (HMP)'
                },
                'housing_location': {
                    'description': 'BXI-H-2-001',
                    'levels': [
                        {'type': 'Wing', 'value': 'H'},
                        {'type': 'Landing', 'value': '2'},
                        {'type': 'Cell', 'value': '001'},
                    ]
                }
            },
            {
                'nomis_id': 'BXI',
                'name': 'BRIXTON (HMP)',
                'housing_location': {
                    'description': 'BXI-H-2-001',
                    'levels': [
                        {'type': 'Wing', 'value': 'H'},
                        {'type': 'Landing', 'value': '2'},
                        {'type': 'Cell', 'value': '001'},
                    ]
                }
            }
        )

    def test_housing_location_level_variations(self):
        self.assertHousingFormatStructure(
            {
                'establishment': {'code': 'HEI', 'desc': 'HMP HEWELL'},
                'housing_location': {
                    'description': 'HEI-1-1-A-001',
                    'levels': [
                        {'type': 'Block', 'value': '1'},
                        {'type': 'Tier', 'value': '1'},
                        {'type': 'Spur', 'value': 'A'},
                        {'type': 'Cell', 'value': '001'},
                    ]
                }
            },
            {
                'nomis_id': 'HEI', 'name': 'HMP HEWELL',
                'housing_location': {
                    'description': 'HEI-1-1-A-001',
                    'levels': [
                        {'type': 'Block', 'value': '1'},
                        {'type': 'Tier', 'value': '1'},
                        {'type': 'Spur', 'value': 'A'},
                        {'type': 'Cell', 'value': '001'},
                    ]
                }
            }
        )
        self.assertHousingFormatStructure(
            {
                'establishment': {'code': 'BZI', 'desc': 'BRONZEFIELD (HMP)'},
                'housing_location': {
                    'description': 'BZI-A-A-001',
                    'levels': [
                        {'type': 'Block', 'value': 'A'},
                        {'type': 'Landing', 'value': 'A'},
                        {'type': 'Cell', 'value': '001'},
                    ]
                }
            },
            {
                'nomis_id': 'BZI', 'name': 'BRONZEFIELD (HMP)',
                'housing_location': {
                    'description': 'BZI-A-A-001',
                    'levels': [
                        {'type': 'Block', 'value': 'A'},
                        {'type': 'Landing', 'value': 'A'},
                        {'type': 'Cell', 'value': '001'},
                    ]
                }
            }
        )

    def test_housing_location_absent_levels(self):
        self.assertHousingFormatStructure(
            {
                'establishment': {'code': 'WWI', 'desc': 'WANDSWORTH (HMP)'},
                'housing_location': {
                    'description': 'WWI-COURT',
                }
            },
            {
                'nomis_id': 'WWI', 'name': 'WANDSWORTH (HMP)',
                'housing_location': {
                    'description': 'WWI-COURT',
                    'levels': []
                }
            }
        )

    def test_housing_location_absent_description(self):
        self.assertHousingFormatStructure(
            {
                'establishment': {'code': 'HEI', 'desc': 'HMP HEWELL'},
                'housing_location': {
                    'levels': [
                        {'type': 'Block', 'value': '1'},
                        {'type': 'Tier', 'value': '1'},
                        {'type': 'Spur', 'value': 'A'},
                        {'type': 'Cell', 'value': '001'},
                    ]
                }
            },
            {
                'nomis_id': 'HEI', 'name': 'HMP HEWELL',
                'housing_location': {
                    'description': 'HEI-1-1-A-001',
                    'levels': [
                        {'type': 'Block', 'value': '1'},
                        {'type': 'Tier', 'value': '1'},
                        {'type': 'Spur', 'value': 'A'},
                        {'type': 'Cell', 'value': '001'},
                    ]
                }
            }
        )
