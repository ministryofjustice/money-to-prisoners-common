import datetime
from importlib import reload
import json
from unittest import mock

from django.conf import settings
from django.test.testcases import SimpleTestCase
import responses

from mtp_common.auth import api_client, urljoin
from mtp_common.auth.exceptions import Unauthorized
from mtp_common.auth.test_utils import generate_tokens


class AuthenticateTestCase(SimpleTestCase):

    @responses.activate
    def test_invalid_credentials_raise_unauthorized(self):
        # mock the response, return 401
        responses.add(
            responses.POST,
            api_client.get_request_token_url(),
            status=401,
            content_type='application/json'
        )

        self.assertRaises(
            Unauthorized, api_client.authenticate, 'my-username', 'invalid-password'
        )

    @responses.activate
    def test_success(self):
        username = 'my-username'

        # mock the response, return token
        expected_token = generate_tokens()
        expected_user_data = {
            'pk': 1,
            'first_name': 'My First Name',
            'last_name': 'My last name',
        }

        responses.add(
            responses.POST,
            urljoin(settings.API_URL, 'oauth2/token'),
            body=json.dumps(expected_token),
            status=200,
            content_type='application/json'
        )

        responses.add(
            responses.GET,
            urljoin(settings.API_URL, 'users/', username),
            body=json.dumps(expected_user_data),
            status=200,
            content_type='application/json'
        )

        # authenticate, should return authentication data
        data = api_client.authenticate(username, 'my-password')

        self.assertEqual(data['pk'], expected_user_data.get('pk'))
        self.assertDictEqual(data['token'], expected_token)
        self.assertDictEqual(data['user_data'], expected_user_data)

    def test_http_instead_of_https_raises_insecure_transport_error(self):
        """
        Test that if env var OAUTHLIB_INSECURE_TRANSPORT == False
        `authenticate` raises an exception if accessing the api
        using http instead of https.
        """
        from oauthlib.oauth2.rfc6749.errors import InsecureTransportError

        with mock.patch.dict(
            'os.environ', {'OAUTHLIB_INSECURE_TRANSPORT': ''}
        ):
            self.assertRaises(
                InsecureTransportError, api_client.authenticate,
                'my-username', 'my-password'
            )

    @responses.activate
    def test_base_api_url_allows_trailing_slash(self):
        actual_api_url = settings.API_URL
        # set API_URL and then reload the client to generate
        # a new REQUEST_TOKEN_URL
        settings.API_URL = actual_api_url + '/'
        reload(api_client)

        username = 'my-username'

        # mock the response, return token
        expected_token = generate_tokens()
        expected_user_data = {
            'pk': 1,
            'first_name': 'My First Name',
            'last_name': 'My last name',
        }

        responses.add(
            responses.POST,
            urljoin(actual_api_url, 'oauth2/token/'),
            body=json.dumps(expected_token),
            status=200,
            content_type='application/json'
        )

        responses.add(
            responses.GET,
            urljoin(actual_api_url, 'users/', username),
            body=json.dumps(expected_user_data),
            status=200,
            content_type='application/json'
        )

        # authenticate, should complete without error
        api_client.authenticate(username, 'my-password')

        # revert changes
        settings.API_URL = actual_api_url
        reload(api_client)


class GetConnectionTestCase(SimpleTestCase):

    def setUp(self):
        """
        Sets up a request mock object with
        request.user.token == generated token.

        It also defines the {base_url}/test/ endpoint which will be
        used by all the test methods.
        """
        super(GetConnectionTestCase, self).setUp()
        self.request = mock.MagicMock(
            user=mock.MagicMock(
                token=generate_tokens()
            )
        )

        self.test_endpoint = urljoin(settings.API_URL, 'test')

    def _test_failure(self):
        conn = api_client.get_connection(self.request)
        self.assertRaises(
            Unauthorized, conn.test.get
        )

    def _test_success(self):
        conn = api_client.get_connection(self.request)
        return conn.test.get()

    def test_without_logged_in_user_raises_unauthorized(self):
        """
        If request.user is None, the get_connection raises
        Unauthorized.
        """
        self.request.user = None

        self.assertRaises(
            Unauthorized, api_client.get_connection, self.request
        )

    @responses.activate
    def test_refresh_token_failing_raises_unauthorized(self):
        def build_expires_at(dt):
            return (
                dt - datetime.datetime(1970, 1, 1)
            ).total_seconds()

        # dates
        now = datetime.datetime.now()
        one_day_delta = datetime.timedelta(days=1)

        expired_yesterday = build_expires_at(now - one_day_delta)

        # set access_token.expires_at to yesterday
        self.request.user.token['expires_at'] = expired_yesterday

        # mock the refresh token endpoint, return 401
        responses.add(
            responses.POST,
            api_client.get_request_token_url(),
            status=401,
            content_type='application/json'
        )

        self._test_failure()

    @responses.activate
    def test_invalid_access_token_raises_unauthorized(self):
        # mock the response, return 401
        responses.add(
            responses.GET,
            self.test_endpoint,
            status=401,
            content_type='application/json'
        )

        self._test_failure()

    @responses.activate
    def test_with_valid_access_token(self):
        # mock the response, return valid body
        expected_response = {'success': True}

        responses.add(
            responses.GET,
            self.test_endpoint,
            body=json.dumps(expected_response),
            status=200,
            content_type='application/json'
        )

        # should return the same generated body
        result = self._test_success()

        self.assertDictEqual(result, expected_response)

    @responses.activate
    def test_token_refreshed_automatically(self):
        """
        Test that if I call the /test/ endpoint with an
        expired access token, the module should automatically:

        - request a new access token
        - update request.user.token to the new token
        - finally request /test/ with the new valid token
        """
        def build_expires_at(dt):
            return (
                dt - datetime.datetime(1970, 1, 1)
            ).total_seconds()

        # dates
        now = datetime.datetime.now()
        one_day_delta = datetime.timedelta(days=1)

        expired_yesterday = build_expires_at(now - one_day_delta)
        expires_tomorrow = build_expires_at(now + one_day_delta)

        # set access_token.expires_at to yesterday
        self.request.user.token['expires_at'] = expired_yesterday
        expired_token = self.request.user.token

        # mock the refresh token endpoint, return a new token
        new_token = generate_tokens(expires_at=expires_tomorrow)
        responses.add(
            responses.POST,
            api_client.get_request_token_url(),
            body=json.dumps(new_token),
            status=200,
            content_type='application/json'
        )

        # mock the /test/ endpoint, return valid body
        expected_response = {'success': True}
        responses.add(
            responses.GET,
            self.test_endpoint,
            body=json.dumps(expected_response),
            status=200,
            content_type='application/json'
        )

        result = self._test_success()

        self.assertDictEqual(result, expected_response)
        self.assertDictEqual(self.request.user.token, new_token)
        self.assertNotEqual(
            expired_token['access_token'],
            new_token['access_token']
        )


class GetApiSessionTestCase(GetConnectionTestCase):

    def _test_failure(self):
        session = api_client.get_api_session(self.request)
        self.assertRaises(
            Unauthorized, session.get, 'test/'
        )

    def _test_success(self):
        session = api_client.get_api_session(self.request)
        response = session.get('test/')
        return response.json()

    def test_without_logged_in_user_raises_unauthorized(self):
        """
        If request.user is None, the get_api_session raises
        Unauthorized.
        """
        self.request.user = None

        self.assertRaises(
            Unauthorized, api_client.get_api_session, self.request
        )
