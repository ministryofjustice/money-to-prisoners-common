from django.conf import settings
from django.test import SimpleTestCase
import responses

from mtp_common.auth import urljoin
from mtp_common.nomis import NomisClient


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

            client = NomisClient()
            balances = client.get_account_balances('BMI', 'A1471AE')
            self.assertEqual(balances, {'cash': 500, 'savings': 0, 'spends': 25})
