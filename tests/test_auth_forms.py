from unittest import mock

from django.conf import settings
from django.test.testcases import SimpleTestCase
from django.utils.encoding import force_text

from mtp_common.auth.forms import (
    AuthenticationForm, PasswordChangeForm, ResetPasswordForm, RESET_CODE_PARAM
)


@mock.patch('mtp_common.auth.forms.authenticate')
class AuthenticationFormTestCase(SimpleTestCase):
    """
    Tests that the AuthenticationForm manages valid/invalid
    credentials and problems with the api.

    Mocks the `authenticate` method so that we can use it
    everywhere in our test methods.
    """

    def setUp(self):
        self.credentials = {
            'username': 'testclient',
            'password': 'password',
        }

    def test_invalid_credentials(self, mocked_authenticate):
        """
        The User submits invalid credentials
        """
        mocked_authenticate.return_value = None

        data = {
            'username': 'jsmith_does_not_exist',
            'password': 'test123',
        }

        form = AuthenticationForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            [force_text(form.error_messages['invalid_login'])]
        )

        mocked_authenticate.assert_called_with(**data)

    def test_success(self, mocked_authenticate):
        """
        Successful authentication.
        """
        mocked_authenticate.return_value = mock.MagicMock()

        form = AuthenticationForm(data=self.credentials)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.non_field_errors(), [])

        mocked_authenticate.assert_called_with(**self.credentials)


@mock.patch('mtp_common.auth.forms.api_client')
class PasswordChangeFormTestCase(SimpleTestCase):

    def test_change_password(self, mock_api_client):
        conn = mock_api_client.get_connection()

        form = PasswordChangeForm(
            None,
            data={
                'old_password': 'old',
                'new_password': 'new',
                'new_password_confirmation': 'new'
            }
        )

        self.assertTrue(form.is_valid())
        conn.change_password.post.assert_called_once_with({
            'old_password': 'old', 'new_password': 'new'
        })

    def test_non_matching_new_passwords_fail(self, mock_api_client):
        conn = mock_api_client.get_connection()

        form = PasswordChangeForm(
            None,
            data={
                'old_password': 'old',
                'new_password': 'new1',
                'new_password_confirmation': 'new2'
            }
        )

        self.assertFalse(form.is_valid())
        self.assertFalse(conn.change_password.post.called)


@mock.patch('mtp_common.auth.forms.api_client')
class ResetPasswordFormTestCase(SimpleTestCase):
    def test_reset_password(self, mock_api_client):
        password_change_url = '/change_password'
        form = ResetPasswordForm(password_change_url=password_change_url, request=None, data={
            'username': 'admin'
        })
        self.assertTrue(form.is_valid())

        reset_password = mock_api_client.get_unauthenticated_connection().reset_password
        reset_password.post.assert_called_once_with({
            'username': 'admin',
            'create_password': {
                'password_change_url': settings.SITE_URL + password_change_url,
                'reset_code_param': RESET_CODE_PARAM
            }
        })
