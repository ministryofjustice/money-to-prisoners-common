from django.conf import settings
from django.test import SimpleTestCase
from requests.exceptions import ConnectionError
import responses

from mtp_common.auth import urljoin
from mtp_common import nomis


class NomisApiTestCase(SimpleTestCase):

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
