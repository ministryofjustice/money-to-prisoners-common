from functools import partial
import os
from urllib.parse import urlsplit

from django.conf import settings
from django.utils.translation import get_language
from oauthlib.oauth2 import LegacyApplicationClient
import requests
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
import slumber

from . import update_token_in_session, urljoin
from .exceptions import (
    Unauthorized, Forbidden, HttpNotFoundError, HttpClientError, HttpServerError
)


# set insecure transport depending on settings val
if getattr(settings, 'OAUTHLIB_INSECURE_TRANSPORT', False):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def get_request_token_url():
    return urljoin(settings.API_URL, '/oauth2/token/')


def get_revoke_token_url():
    return urljoin(settings.API_URL, '/oauth2/revoke_token/')


class LocalisedOAuth2Session(OAuth2Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'Accept-Language' not in self.headers:
            self.headers['Accept-Language'] = get_language() or settings.LANGUAGE_CODE


def create_http_exception(response, exception_type):
    return exception_type(
        'Status code {code} for {url}'.format(
            code=response.status_code,
            url=response.url
        ),
        content=response.content if hasattr(response, 'content') else None,
        response=response
    )


def auth_failure_response_hook(response, *args, **kwargs):
    if response.status_code == 401:
        raise create_http_exception(response, Unauthorized)
    if response.status_code == 403:
        raise create_http_exception(response, Forbidden)
    return response


def error_status_response_hook(response, *args, **kwargs):
    response = auth_failure_response_hook(response, *args, **kwargs)
    if response.status_code == 404:
        raise create_http_exception(response, HttpNotFoundError)
    if response.status_code >= 400 and response.status_code <= 499:
        raise create_http_exception(response, HttpClientError)
    if response.status_code >= 500 and response.status_code <= 599:
        raise create_http_exception(response, HttpServerError)
    return response


class MoJOAuth2Session(LocalisedOAuth2Session):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hooks['response'] = [error_status_response_hook]
        self.base_url = settings.API_URL

    def request(self, method, url, data=None, headers=None, **kwargs):
        if self.base_url and not urlsplit(url).scheme:
            url = urljoin(self.base_url, url)
        kwargs.setdefault('timeout', 30)
        return super().request(method, url, data=data, headers=headers, **kwargs)


def authenticate(username, password):
    """
    Returns:
        a dict with:
            pk: the pk of the user
            token: dict containing all the data from the api
                (access_token, refresh_token, expires_at etc.)
            user_data: dict containing user data such as
                first_name, last_name etc.
        if the authentication succeeds
        Raises Unauthorized if the authentication fails
    """
    session = MoJOAuth2Session(
        client=LegacyApplicationClient(
            client_id=settings.API_CLIENT_ID
        )
    )

    token = session.fetch_token(
        token_url=get_request_token_url(),
        username=username,
        password=password,
        auth=HTTPBasicAuth(settings.API_CLIENT_ID, settings.API_CLIENT_SECRET),
        timeout=30,
        encoding='utf-8'
    )

    user_data = session.get('/users/{username}/'.format(username=username)).json()

    return {
        'pk': user_data.get('pk'),
        'token': token,
        'user_data': user_data
    }


def revoke_token(access_token):
    """
    Instructs the API to delete this access token and associated refresh token
    """
    response = requests.post(
        get_revoke_token_url(),
        data={
            'token': access_token,
            'client_id': settings.API_CLIENT_ID,
            'client_secret': settings.API_CLIENT_SECRET,
        },
        timeout=30
    )
    return response.status_code == 200


def get_api_session(request):
    return get_api_session_with_session(request.user, request.session)


def get_api_session_with_session(user, session):
    if not user:
        raise Unauthorized('no such user')

    def token_saver(token, session, user):
        user.token = token
        update_token_in_session(session, token)

    session = MoJOAuth2Session(
        settings.API_CLIENT_ID,
        token=user.token,
        auto_refresh_url=get_request_token_url(),
        auto_refresh_kwargs={
            'client_id': settings.API_CLIENT_ID,
            'client_secret': settings.API_CLIENT_SECRET
        },
        token_updater=partial(token_saver, session=session, user=user)
    )

    return session


def get_authenticated_api_session(username, password):
    """
    :return: an authenticated api session
    """
    session = MoJOAuth2Session(
        client=LegacyApplicationClient(
            client_id=settings.API_CLIENT_ID
        )
    )

    session.fetch_token(
        token_url=get_request_token_url(),
        username=username,
        password=password,
        auth=HTTPBasicAuth(settings.API_CLIENT_ID, settings.API_CLIENT_SECRET),
        timeout=30,
        encoding='utf-8'
    )
    return session


def get_unauthenticated_session():
    return MoJOAuth2Session()


# slumber connection methods


def get_connection(request):
    """
    Returns a slumber connection configured using the token of the logged-in user.

    It raises `Unauthorized` if the user is not authenticated.

    ```
    response = get_connection(request).my_endpoint.get()
    ```
    """
    return get_connection_with_session(request.user, request.session)


def get_connection_with_session(user, session):
    """
    Returns a slumber connection configured using the token of the user.

    It raises `Unauthorized` if the user is not authenticated.

    ```
    response = get_connection(user, session).my_endpoint.get()
    ```
    """
    session = get_api_session_with_session(user, session)
    return _get_slumber_connection(session)


def get_authenticated_connection(username, password):
    """
    :return: an authenticated slumber connection
    """
    session = get_authenticated_api_session(username, password)
    return _get_slumber_connection(session)


def get_unauthenticated_connection():
    """
    :return: an unauthenticated slumber connection
    """
    return _get_slumber_connection(None)


def _get_slumber_connection(session):
    if session:
        session.hooks['response'] = [auth_failure_response_hook]
        session.base_url = None
    return slumber.API(
        base_url=settings.API_URL, session=session
    )
