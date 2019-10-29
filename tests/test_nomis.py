from django.conf import settings
from django.test import SimpleTestCase, override_settings
from requests.exceptions import ConnectionError
import responses

from mtp_common import nomis
from mtp_common.auth import urljoin


class LegacyNomisApiTestCase(SimpleTestCase):
    @override_settings(NOMIS_API_CLIENT_TOKEN='abc.abc.abc')
    def test_client_token_taken_from_settings(self):
        self.assertEqual(nomis.connector.get_client_token(), settings.NOMIS_API_CLIENT_TOKEN)
        self.assertTrue(nomis.can_access_nomis())

    @override_settings(NOMIS_API_CLIENT_TOKEN='')
    def test_cannot_access_nomis_without_token(self):
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

    def assertHousingFormatStructure(self, nomis_mocked_response, expected_location_dict):  # noqa: N802
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                urljoin(settings.NOMIS_API_BASE_URL, '/offenders/A1401AE/location/'),
                json=nomis_mocked_response
            )
            actual_location_dict = nomis.get_location('A1401AE')
        self.assertEqual(actual_location_dict, expected_location_dict)

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
