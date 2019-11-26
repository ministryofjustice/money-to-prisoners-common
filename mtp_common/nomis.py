import base64
import datetime
import logging
import time
from abc import ABC, abstractmethod
from urllib.parse import quote_plus

from django.conf import settings
from django.core.cache import cache
import jwt
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
    def get_bearer_token(self):
        """
        :return: bearer token to be used in API calls.
        """

    @abstractmethod
    def can_access_nomis(self):
        """
        :return: True if this class has all the elements in place to connect to NOMIS.
        """

    def build_request_api_headers(self):
        """
        :return: dict with headers to used in calls to the NOMIS API.
        """
        bearer_token = self.get_bearer_token()
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {bearer_token}',
        }

    def request(self, verb, path, params=None, json=None, timeout=15, retries=0, session=None):
        """
        Makes a request call to NOMIS.
        You probably want to use the `get` or the `post` methods instead.
        """
        response = request_retry(
            verb,
            self.build_nomis_api_url(path),
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
    TODO: Remove once all apps move to NOMIS Elite2
    """

    def get_client_token(self):
        return getattr(settings, 'NOMIS_API_CLIENT_TOKEN', None)

    def build_nomis_api_url(self, path):
        return urljoin(settings.NOMIS_API_BASE_URL, path)

    def get_bearer_token(self):
        encoded = jwt.encode(
            {
                'iat': int(time.time()),
                'token': self.get_client_token(),
            },
            settings.NOMIS_API_PRIVATE_KEY,
            'ES256',
        )
        return encoded.decode('utf8')

    def can_access_nomis(self):
        return bool(
            settings.NOMIS_API_BASE_URL
            and settings.NOMIS_API_PRIVATE_KEY
            and self.get_client_token()
        )


class EliteNomisRetry(Retry):
    """
    A subclass of Retry that deletes the token from the cache and instructs
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
                logger.warning('Deleting the cached NOMIS token because of a 401 response')
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


class EliteNomisConnector(BaseNomisConnector):
    """
    Connector for Elite2 NOMIS auth and API.
    """

    TOKEN_CACHE_KEY = 'NOMIS_TOKEN'

    def _build_nomis_url(self, *path):
        """
        Can be used to build both auth and API urls.
        """
        return urljoin(settings.NOMIS_ELITE_BASE_URL, *path, trailing_slash=False)

    def build_nomis_api_url(self, path):
        return self._build_nomis_url('/elite2api/api/v1', path)

    def _get_new_token_data(self):
        """
        Gets a new token from NOMIS.
        """
        creds = base64.b64encode(
            f'{settings.NOMIS_ELITE_CLIENT_ID}:{settings.NOMIS_ELITE_CLIENT_SECRET}'.encode('utf8')
        ).decode('utf8')

        response = request_retry(
            'post',
            self._build_nomis_url('/auth/oauth/token'),
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

    def request(self, verb, path, params=None, json=None, timeout=15, retries=0, session=None):
        """
        Overrides the parent method by retrying the request if it returns 401 after deleting the cached token.
        """
        if not isinstance(retries, Retry):
            retries = EliteNomisRetry(self, retries)

        return super().request(verb, path, params=params, json=json, timeout=timeout, retries=retries, session=session)

    def get_bearer_token(self):
        """
        Gets the bearer token from cache if it exists, or from NOMIS otherwise.
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
        :return: True if this connector has all keys in place to authenticate
        """
        return all(
            getattr(settings, key, None)
            for key in (
                'NOMIS_ELITE_CLIENT_ID',
                'NOMIS_ELITE_CLIENT_SECRET',
                'NOMIS_ELITE_BASE_URL',
            )
        )


def _get_connector():
    """
    :return: the best NOMIS connector that can be used.
    TODO: Remove once all apps move to NOMIS Elite2
    """
    elite_connector = EliteNomisConnector()
    if elite_connector.can_access_nomis():
        return elite_connector

    return LegacyNomisConnector()


connector = _get_connector()


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
