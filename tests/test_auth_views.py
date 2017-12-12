from unittest import mock

from django.conf import settings
from django.http.request import QueryDict
from django.test import SimpleTestCase
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_text
import responses

from mtp_common.auth import SESSION_KEY, BACKEND_SESSION_KEY, \
    AUTH_TOKEN_SESSION_KEY, USER_DATA_SESSION_KEY
from mtp_common.auth import api_client, urljoin
from mtp_common.auth.exceptions import Forbidden
from mtp_common.auth.test_utils import generate_tokens


@mock.patch('mtp_common.auth.backends.api_client')
class LoginViewTestCase(SimpleTestCase):
    """
    Tests that the login flow works as expected.
    """
    login_url = reverse_lazy('login')

    def test_success(self, mocked_api_client):
        """
        Successful authentication.
        """

        user_pk = 100
        credentials = {
            'username': 'my-username',
            'password': 'my-password'
        }
        token = generate_tokens()
        user_data = {
            'first_name': 'My First Name',
            'last_name': 'My Last Name',
            'username': credentials['username'],
        }
        mocked_api_client.authenticate.return_value = {
            'pk': user_pk,
            'token': token,
            'user_data': user_data
        }

        # login
        response = self.client.post(
            self.login_url, data=credentials
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session[SESSION_KEY], user_pk
        )
        self.assertEqual(
            self.client.session[BACKEND_SESSION_KEY],
            settings.AUTHENTICATION_BACKENDS[0]
        )
        self.assertDictEqual(
            self.client.session[AUTH_TOKEN_SESSION_KEY], token
        )
        self.assertDictEqual(
            self.client.session[USER_DATA_SESSION_KEY], user_data
        )

    def test_invalid_credentials(self, mocked_api_client):
        """
        The User submits invalid credentials.
        """
        # mock the connection, return invalid credentials
        mocked_api_client.authenticate.return_value = None

        response = self.client.post(
            self.login_url, data={
                'username': 'my-username',
                'password': 'wrong-password'
            }, follow=True
        )

        form = response.context_data['form']
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['__all__'],
            [force_text(form.error_messages['invalid_login'])]
        )
        self.assertEqual(len(self.client.session.items()), 0)  # nothing in the session

    def test_login_fails_without_application_access(self, mocked_api_client):
        """
        The user should be presented with an aproppriate error message if they
        received a forbidden repsonse.
        """
        credentials = {
            'username': 'my-username',
            'password': 'my-password'
        }
        mocked_api_client.authenticate.side_effect = Forbidden

        response = self.client.post(
            self.login_url, data=credentials
        )

        form = response.context_data['form']
        self.assertFalse(form.is_valid(), msg='user should not be able to log in if they are'
                                              'forbidden from accessing that application')
        self.assertEqual(form.errors['__all__'], [force_text(form.error_messages['application_inaccessible'])],
                         msg='user should see error message if they are forbidden'
                             'from accessing that application')


class AuthenticatedTestCase(SimpleTestCase):
    login_url = reverse_lazy('login')

    @mock.patch('mtp_common.auth.backends.api_client')
    def login(self, mocked_api_client):
        user_pk = 100
        credentials = {
            'username': 'my-username',
            'password': 'my-password',
        }
        token = generate_tokens()
        user_data = {
            'first_name': 'My First Name',
            'last_name': 'My Last Name',
            'username': credentials['username'],
        }
        mocked_api_client.authenticate.return_value = {
            'pk': user_pk,
            'token': token,
            'user_data': user_data,
        }

        # login
        response = self.client.post(self.login_url, data=credentials,
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        return token


class LogoutViewTestCase(AuthenticatedTestCase):
    """
    Tests the logout flow works as expected
    """
    logout_url = reverse_lazy('logout')

    def mock_revocation_response(self):
        responses.add(
            responses.POST,
            api_client.get_revoke_token_url(),
            status=200,
            content_type='application/json'
        )

    @responses.activate
    def test_logout_clears_session(self):
        self.login()

        self.mock_revocation_response()

        # logout
        response = self.client.get(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)

        # nothing in the session
        self.assertEqual(len(self.client.session.items()), 0)

    @responses.activate
    def test_logout_triggers_token_revocation_request(self):
        token = self.login()

        self.mock_revocation_response()

        # logout
        response = self.client.get(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)

        # token revocation endpoint called with correct details
        self.assertEqual(len(responses.calls), 1)
        revocation_call = responses.calls[0]
        revocation_call_data = QueryDict(revocation_call.request.body)
        revocation_call_data = dict(
            (key, revocation_call_data.get(key, getattr(mock.sentinel, key)))
            for key in ['token', 'client_id', 'client_secret']
        )
        expected_revocation_call_data = {
            'token': token['access_token'],
            'client_id': settings.API_CLIENT_ID,
            'client_secret': settings.API_CLIENT_SECRET,
        }
        self.assertDictEqual(revocation_call_data, expected_revocation_call_data)


class PasswordChangeViewTestCase(AuthenticatedTestCase):

    @responses.activate
    def test_password_change(self):
        responses.add(
            responses.POST,
            urljoin(settings.API_URL, 'change_password'),
            status=204,
            content_type='application/json'
        )

        self.login()
        response = self.client.post(
            reverse('password_change'), data={
                'old_password': 'old',
                'new_password': 'new',
                'new_password_confirmation': 'new'
            }, follow=False
        )

        self.assertRedirects(response, reverse('password_change_done'))

    @responses.activate
    def test_incorrect_password_errors(self):
        responses.add(
            responses.POST,
            urljoin(settings.API_URL, 'change_password'),
            json={'errors': {'__all__': ['Incorrect password']}},
            status=400,
            content_type='application/json'
        )

        self.login()
        response = self.client.post(
            reverse('password_change'),
            data={
                'old_password': 'wrong',
                'new_password': 'new',
                'new_password_confirmation': 'new'
            }
        )

        form = response.context_data['form']
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['__all__'], ['Incorrect password'])


class ResetPasswordViewTestCase(SimpleTestCase):

    @responses.activate
    def test_reset_password(self):
        responses.add(
            responses.POST,
            urljoin(settings.API_URL, 'reset_password'),
            status=204,
            content_type='application/json'
        )

        response = self.client.post(
            reverse('reset_password'),
            data={
                'username': 'admin',
            }, follow=False
        )
        self.assertRedirects(response, reverse('reset_password_done'))

    @responses.activate
    def test_reset_password_errors(self):
        responses.add(
            responses.POST,
            urljoin(settings.API_URL, 'reset_password'),
            json={'errors': {'username': ['User not found']}},
            status=400,
            content_type='application/json'
        )

        response = self.client.post(
            reverse('reset_password'),
            data={
                'username': 'unknown',
            }, follow=True
        )
        form = response.context_data['form']
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['username'], ['User not found'])
