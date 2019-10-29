import datetime
import logging
import time
from abc import ABC, abstractmethod
from urllib.parse import quote_plus

from django.conf import settings
import jwt
import requests
from requests.exceptions import ConnectionError

from mtp_common.auth import urljoin

logger = logging.getLogger('mtp')


class BaseNomisConnector(ABC):
    """
    Abstract class that connects to NOMIS; to be sublassed.
    """

    @abstractmethod
    def build_nomis_api_url(self, path):
        """
        :return: the url to the API endpoint defined by `path`.
        :param path: string defining the endpoint e.g. '/some/endpoint'
        """

    @abstractmethod
    def build_request_api_headers(self):
        """
        :return: dict with headers to used in calls to the NOMIS API.
        """

    @abstractmethod
    def can_access_nomis(self):
        """
        :return: True if this class can connect to NOMIS.
        """

    def request(self, verb, path, params=None, json=None, timeout=15, retries=0, session=None):
        """
        Makes a request call to NOMIS.
        You probably want to use the `get` or the `post` methods instead.
        """
        session_or_module = session or requests

        method = getattr(session_or_module, verb)
        should_retry = False
        try:
            response = method(
                self.build_nomis_api_url(path),
                headers=self.build_request_api_headers(),
                timeout=timeout,
                params=params,
                json=json,
            )
        except ConnectionError as e:
            if retries > 0:
                should_retry = True
            else:
                raise e
        else:
            if response.status_code >= 500 and retries > 0:
                should_retry = True

        if should_retry:
            return self.request(
                verb,
                path,
                params=params,
                json=json,
                timeout=timeout,
                retries=retries-1,
                session=session,
            )

        response.raise_for_status()
        if response.status_code != requests.codes.no_content:
            return response.json()

        return {
            'status_code': response.status_code,
        }

    def get(self, path, params=None, timeout=15, retries=0, session=None):
        """
        Makes a GET request to NOMIS.
        """
        if params:
            params = {
                param: params[param]
                for param in params
                if params[param] is not None
            }
        return self.request('get', path, params=params, timeout=timeout, retries=retries, session=session)

    def post(self, path, data=None, timeout=15, retries=0, session=None):
        """
        Makes a POST request to NOMIS.
        """
        return self.request('post', path, json=data, timeout=timeout, retries=retries, session=session)


class LegacyNomisConnector(BaseNomisConnector):
    """
    Connector for legacy NOMIS auth and API.
    """

    def get_client_token(self):
        return getattr(settings, 'NOMIS_API_CLIENT_TOKEN', None)

    def build_nomis_api_url(self, path):
        return urljoin(settings.NOMIS_API_BASE_URL, path)

    def build_request_api_headers(self):
        encoded = jwt.encode(
            {
                'iat': int(time.time()),
                'token': self.get_client_token(),
            },
            settings.NOMIS_API_PRIVATE_KEY,
            'ES256',
        )
        bearer_token = encoded.decode('utf8')
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {bearer_token}',
        }

    def can_access_nomis(self):
        return bool(
            settings.NOMIS_API_BASE_URL
            and settings.NOMIS_API_PRIVATE_KEY
            and self.get_client_token()
        )


connector = LegacyNomisConnector()


def can_access_nomis():
    return connector.can_access_nomis()


def convert_date_param(param):
    if isinstance(param, datetime.date):
        return param.isoformat()
    elif isinstance(param, str):
        return param
    return None


def get_account_balances(prison_id, prisoner_number, retries=0, session=None):
    return connector.get(
        '/prison/{prison_id}/offenders/{prisoner_number}/accounts'.format(
            prison_id=quote_plus(prison_id),
            prisoner_number=quote_plus(prisoner_number)
        ),
        retries=retries, session=session
    )


def get_transaction_history(prison_id, prisoner_number, account_code,
                            from_date, to_date=None, retries=0, session=None):
    params = {
        'from_date': convert_date_param(from_date),
        'to_date': convert_date_param(to_date),
    }
    return connector.get(
        '/prison/{prison_id}/offenders/{prisoner_number}/accounts/{account_code}/transactions'.format(
            prison_id=quote_plus(prison_id),
            prisoner_number=quote_plus(prisoner_number),
            account_code=quote_plus(account_code)
        ),
        params=params, retries=retries, session=session
    )


def create_transaction(prison_id, prisoner_number, amount, record_id,
                       description, transaction_type, retries=0, session=None):
    data = {
        'type': transaction_type,
        'description': description,
        'amount': amount,
        'client_transaction_id': str(record_id),
        'client_unique_ref': str(record_id)
    }
    return connector.post(
        '/prison/{prison_id}/offenders/{prisoner_number}/transactions'.format(
            prison_id=quote_plus(prison_id),
            prisoner_number=quote_plus(prisoner_number)
        ),
        data, retries=retries, session=session
    )


def get_photograph_data(prisoner_number, retries=0, session=None):
    result = connector.get(
        '/offenders/{prisoner_number}/image'.format(
            prisoner_number=quote_plus(prisoner_number)
        ),
        retries=retries, session=session
    )
    if result.get('image'):
        return result['image']


def get_location(prisoner_number, retries=0, session=None):
    result = connector.get(
        '/offenders/{prisoner_number}/location'.format(
            prisoner_number=quote_plus(prisoner_number)
        ),
        retries=retries, session=session
    )
    if 'establishment' in result:
        location = {
            'nomis_id': result['establishment']['code'],
            'name': result['establishment']['desc'],
        }
        if isinstance(result.get('housing_location'), dict):
            housing = result['housing_location']
            if 'levels' not in housing:
                # ensure levels key is present
                housing['levels'] = []
            if 'description' not in housing:
                # synthesise missing description
                housing['description'] = location['nomis_id']
                if housing['levels']:
                    housing['description'] += (
                        '-' +
                        '-'.join(level['value'] for level in housing['levels'])
                    )
            location['housing_location'] = housing
        return location
