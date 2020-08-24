"""
This module is used to access data in NOMIS (the database that hold all information in prisons).

HMPPS has split the functionality that used to be in one API (called NOMIS or Elite2 in the past) into:
- HMPPS Auth for authenticating all API calls
- Prison API for accessing NOMIS-specific endpoints
- and other services we do not currently use

The Prison API includes "V1" endpoints (the only endpoints we use) which are from a much older "NOMIS API".

Prisoner money apps are currently only interested in NOMIS data hence this module is still called `nomis`.
If in future we need to consume other HMPPS apis, it may make sense to split this module into separate components.
"""

import base64
import datetime
import logging
from urllib.parse import quote_plus

from django.conf import settings
from django.core.cache import cache
import requests
from requests.exceptions import ConnectionError

from mtp_common.auth import urljoin

logger = logging.getLogger('mtp')


class Retry:
    """
    Object to be used with `request_retry`.
    It configures some retry options and can be subclassed to customise related logic.
    """
    def __init__(
        self,
        max_retries,
        retry_on_status=(
            408,  # Request Timeout
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        ),
    ):

        self.max_retries = max_retries
        self.retry_on_status = retry_on_status
        self.retry_count = 0

    def should_retry(self, exception=None, response=None):
        """
        :return: True if the caller should retry the same request.
        :exception Exception: any raised exception
        :response HTTPResponse: any response returned, including successful ones.
        """
        if response is not None and response.status_code not in self.retry_on_status:
            return False
        return (self.max_retries - self.retry_count) > 0

    def before_retrying(self, request_kwargs):
        """
        Callback called before retrying.
        """
        self.retry_count += 1


def request_retry(
    verb,
    *args,
    retries=0,
    session=None,
    **kwargs,
):
    """
    Like requests but with the ability to retry a request.
    `retries` can be a number or an instance of `mtp_common.nomis.Retry`.

    The logic doesn't use the session.mount + urllib3 Retry because we want to configure the retry count per-call
    instead of per-session and because we want to customise the retry logic.
    """
    if not isinstance(retries, Retry):
        retries = Retry(retries)

    session_or_module = session or requests

    method = getattr(session_or_module, verb)
    should_retry = False
    try:
        response = method(*args, **kwargs)
    except ConnectionError as e:
        should_retry = retries.should_retry(exception=e)
        if not should_retry:
            raise e
    else:
        should_retry = retries.should_retry(response=response)

    if should_retry:
        retries.before_retrying(kwargs)
        return request_retry(
            verb,
            *args,
            retries=retries,
            session=session,
            **kwargs,
        )

    return response


class AuthenticatedRetry(Retry):
    """
    A subclass of Retry that deletes the HMPPS Auth token from the cache and instructs
    the caller to retry again if the status code of the response is 401.

    This is to cache the (hopefully) rare case where the cached token is not valid.
    """
    def __init__(self, connector, *args, **kwargs):
        self.connector = connector
        super().__init__(*args, **kwargs)

    def should_retry(self, exception=None, response=None):
        """
        If we haven't retried yet and response.status_code == 401, delete the cached token and retry again.
        """
        if self.retry_count == 0:
            if response is not None and response.status_code == 401:
                logger.warning('Deleting the cached HMPPS Auth token because of a 401 response')
                cache.delete(self.connector.TOKEN_CACHE_KEY)
                return True
        return super().should_retry(exception=exception, response=response)

    def before_retrying(self, request_kwargs):
        """
        Re-builds the headers if the token can't be find in the cache.
        """
        if not cache.get(self.connector.TOKEN_CACHE_KEY):
            request_kwargs['headers'] = self.connector.build_request_api_headers()

        super().before_retrying(request_kwargs)


class Connector:
    """
    Connector for HMPPS Prison API (using HMPPS Auth)
    """
    TOKEN_CACHE_KEY = 'NOMIS_TOKEN'

    @property
    def hmpps_auth_token_url(self):
        return urljoin(settings.HMPPS_AUTH_BASE_URL, '/oauth/token', trailing_slash=False)

    @property
    def prison_api_v1_base_url(self):
        return urljoin(settings.HMPPS_PRISON_API_BASE_URL, '/api/v1', trailing_slash=False)

    def build_request_api_headers(self):
        """
        :return: dict with headers to used in calls to the Prison API (i.e. NOMIS).
        """
        bearer_token = self.get_bearer_token()
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {bearer_token}',
        }

    def request(self, verb, path, params=None, json=None, timeout=15, retries=0, session=None):
        """
        Makes a request call to Prison API (i.e. NOMIS).
        You probably want to use the `get` or the `post` methods instead.
        """
        if not isinstance(retries, Retry):
            retries = AuthenticatedRetry(self, retries)

        response = request_retry(
            verb,
            urljoin(self.prison_api_v1_base_url, path, trailing_slash=False),
            retries=retries,
            session=session,
            headers=self.build_request_api_headers(),
            timeout=timeout,
            params=params,
            json=json,
        )

        response.raise_for_status()

        if response.status_code != requests.codes.no_content:
            return response.json()

        return {
            'status_code': response.status_code,
        }

    def get(self, path, params=None, timeout=15, retries=0, session=None):
        """
        Makes a GET request to Prison API (i.e. NOMIS).
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
        Makes a POST request to Prison API (i.e. NOMIS).
        """
        return self.request('post', path, json=data, timeout=timeout, retries=retries, session=session)

    def _get_new_token_data(self):
        """
        Gets a new token using HMPPS Auth.

        :return: bearer token to be used in API calls.
        """
        creds = base64.b64encode(
            f'{settings.HMPPS_CLIENT_ID}:{settings.HMPPS_CLIENT_SECRET}'.encode('utf8')
        ).decode('utf8')

        response = request_retry(
            'post',
            self.hmpps_auth_token_url,
            retries=3,
            params={
                'grant_type': 'client_credentials',
            },
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Content-Length': '0',
                'Authorization': f'Basic {creds}',
            },
            timeout=10,
        )
        response.raise_for_status()

        return response.json()

    def get_bearer_token(self):
        """
        Gets the bearer token from cache if it exists, or from HMPPS Auth otherwise.

        :return: bearer token to be used in API calls.
        """
        token = cache.get(self.TOKEN_CACHE_KEY)
        if not token:
            token_data = self._get_new_token_data()
            token = token_data['access_token']

            cache_expire_in = token_data['expires_in'] - (60 * 5)  # -5 mins just to avoid disalignment
            cache.set(self.TOKEN_CACHE_KEY, token, timeout=cache_expire_in)
        return token

    def can_access_nomis(self):
        """
        :return: True if this connector has all keys in place to connect to Prison API (i.e. NOMIS).
        """
        return all(
            getattr(settings, key, None)
            for key in (
                'HMPPS_CLIENT_ID',
                'HMPPS_CLIENT_SECRET',
                'HMPPS_AUTH_BASE_URL',
                'HMPPS_PRISON_API_BASE_URL',
            )
        )


connector = Connector()


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
        retries=retries,
        session=session,
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
        params=params,
        retries=retries,
        session=session,
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
        data,
        retries=retries,
        session=session,
    )


def get_photograph_data(prisoner_number, retries=0, session=None):
    result = connector.get(
        '/offenders/{prisoner_number}/image'.format(
            prisoner_number=quote_plus(prisoner_number)
        ),
        retries=retries,
        session=session,
    )

    return result.get('image', None)


def get_location(prisoner_number, retries=0, session=None):
    result = connector.get(
        '/offenders/{prisoner_number}/location'.format(
            prisoner_number=quote_plus(prisoner_number)
        ),
        retries=retries,
        session=session,
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
    return None
