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
    return None


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
        encoded = jwt.encode(
            {'iat': int(time.time()), 'token': settings.NOMIS_API_CLIENT_TOKEN},
            settings.NOMIS_API_PRIVATE_KEY, 'ES256'
        )
        self.bearer_token = encoded.decode('utf8')

    def get(self, path, params=None, timeout=15):
        if params:
            params = {
                param: params[param] for param in params
                if params[param] is not None
            }
        response = requests.get(
            self._build_url(path),
            params=params,
            headers=self._headers,
            timeout=timeout
        )
        response.raise_for_status()
        if response.status_code != requests.codes.no_content:
            return response.json()
        return {'status_code': response.status_code}

    def post(self, path, data=None, timeout=15):
        response = requests.post(
            self._build_url(path),
            json=data,
            headers=self._headers,
            timeout=timeout
        )
        response.raise_for_status()
        if response.status_code != requests.codes.no_content:
            return response.json()
        return {'status_code': response.status_code}

    def get_account_balances(self, prison_id, prisoner_number):
        return self.get(
            '/prison/{prison_id}/offenders/{prisoner_number}/accounts'.format(
                prison_id=prison_id, prisoner_number=prisoner_number
            )
        )

    def get_transaction_history(self, prison_id, prisoner_number, account_code,
                                from_date, to_date=None):
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
