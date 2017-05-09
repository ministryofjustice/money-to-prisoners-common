from functools import partial
import os

from django.conf import settings
from django.utils.translation import get_language
from oauthlib.oauth2 import LegacyApplicationClient
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from requests_oauthlib import OAuth2Session
import slumber

from . import update_token_in_session, urljoin
from .exceptions import Unauthorized, Forbidden


# set insecure transport depending on settings val
if settings.OAUTHLIB_INSECURE_TRANSPORT:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

REQUEST_TOKEN_URL = urljoin(settings.API_URL, '/oauth2/token/')
REVOKE_TOKEN_URL = urljoin(settings.API_URL, '/oauth2/revoke_token/')


class LocalisedOAuth2Session(OAuth2Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'Accept-Language' not in self.headers:
            self.headers['Accept-Language'] = get_language() or settings.LANGUAGE_CODE


def response_hook(response, *args, **kwargs):
    if response.status_code == 401:
        raise Unauthorized()
    if response.status_code == 403:
        raise Forbidden
    return response


class MoJOAuth2Session(LocalisedOAuth2Session):
    def request(self, method, url, data=None, headers=None, **kwargs):
        hooks = kwargs.get('hooks', {})
        if 'response' not in hooks:
            hooks['response'] = response_hook
        kwargs['hooks'] = hooks

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
        None if the authentication fails
    """
    session = MoJOAuth2Session(
        client=LegacyApplicationClient(
            client_id=settings.API_CLIENT_ID
        )
    )

    try:
        token = session.fetch_token(
            token_url=REQUEST_TOKEN_URL,
            username=username,
            password=password,
            auth=HTTPBasicAuth(settings.API_CLIENT_ID, settings.API_CLIENT_SECRET),
            timeout=15,
            encoding='utf-8'
        )

        conn = _get_slumber_connection(session)
        user_data = conn.users(username).get()

        return {
            'pk': user_data.get('pk'),
            'token': token,
            'user_data': user_data
        }
    except HTTPError as e:
        # return None if response.status_code == 401
        #   => invalid credentials
        if hasattr(e, 'response') and e.response.status_code == 401:
            return None
        raise e


def revoke_token(access_token):
    """
    Instructs the API to delete this access token and associated refresh token
    """
    response = requests.post(
        REVOKE_TOKEN_URL,
        data={
            'token': access_token,
            'client_id': settings.API_CLIENT_ID,
            'client_secret': settings.API_CLIENT_SECRET,
        },
        timeout=15
    )
    return response.status_code == 200


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
    if not user:
        raise Unauthorized(u'no such user')

    def token_saver(token, session, user):
        user.token = token
        update_token_in_session(session, token)

    session = MoJOAuth2Session(
        settings.API_CLIENT_ID,
        token=user.token,
        auto_refresh_url=REQUEST_TOKEN_URL,
        auto_refresh_kwargs={
            'client_id': settings.API_CLIENT_ID,
            'client_secret': settings.API_CLIENT_SECRET
        },
        token_updater=partial(token_saver, session=session, user=user)
    )

    return _get_slumber_connection(session)


def get_authenticated_connection(username, password):
    """
    :return: an authenticated slumber connection
    """
    session = LocalisedOAuth2Session(
        client=LegacyApplicationClient(
            client_id=settings.API_CLIENT_ID
        )
    )

    session.fetch_token(
        token_url=REQUEST_TOKEN_URL,
        username=username,
        password=password,
        auth=HTTPBasicAuth(settings.API_CLIENT_ID, settings.API_CLIENT_SECRET),
        timeout=15,
        encoding='utf-8'
    )

    return _get_slumber_connection(session)


def get_unauthenticated_connection():
    """
    :return: an unauthenticated slumber connection
    """
    return slumber.API(base_url=settings.API_URL)


def _get_slumber_connection(session):
    return slumber.API(
        base_url=settings.API_URL, session=session
    )
