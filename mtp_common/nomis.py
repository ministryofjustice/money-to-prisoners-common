from datetime import date
import time

from django.conf import settings
import jwt
from mtp_common.auth import urljoin
import requests


def convert_date_param(param):
        if isinstance(param, date):
            return param.isoformat()
        elif isinstance(param, str):
            return param
        return ''


class NomisClient():

    def __init__(self):
        self.regenerate_token()

    @property
    def _headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.bearer_token
        }

    def _build_url(self, path):
        return urljoin(settings.NOMIS_API_BASE_URL, path)

    def regenerate_token(self):
        with open(settings.NOMIS_API_TOKEN_FILE) as f:
            client_token = f.read()

        with open(settings.NOMIS_API_PRIVATE_KEY) as f:
            secret_key = f.read()

        encoded = jwt.encode(
            {'iat': int(time.time()), 'token': client_token}, secret_key, 'ES256'
        )
        self.bearer_token = encoded.decode('utf8')

    def get(self, path, params={}, timeout=15):
        return requests.post(
            self._build_url(path),
            params=params,
            headers=self._headers,
            timeout=timeout
        )

    def post(self, path, data, timeout=15):
        return requests.post(
            self._build_url(path),
            json=data,
            headers=self._headers,
            timeout=timeout
        )

    def get_account_balances(self, prison_id, prisoner_number):
        return self.get(
            '/prison/{prison_id}/offenders/{prisoner_number}/accounts'.format(
                prison_id=prison_id, prisoner_number=prisoner_number
            )
        )

    def get_transaction_history(self, prison_id, prisoner_number, account_code,
                                from_date=None, to_date=None):
        params = {
            'from_date': convert_date_param(from_date),
            'to_date': convert_date_param(to_date),
        }
        return self.get(
            '/prison/{prison_id}/offenders/{prisoner_number}/accounts/{account_code}/transactions'.format(
                prison_id=prison_id, prisoner_number=prisoner_number, account_code=account_code
            ),
            params=params
        )

    def credit_prisoner(self, prison_id, prisoner_number, amount, credit_id, description):
        data = {
            'type': 'MTP',
            'description': description,
            'amount': amount,
            'client_transaction_id': 'MTP{credit_id}'.format(credit_id=credit_id),
        }
        return self.post(
            '/prison/{prison_id}/offenders/{prisoner_number}/transactions'.format(
                prison_id=prison_id, prisoner_number=prisoner_number
            ),
            data
        )
