import functools
from unittest import mock

from django.core.exceptions import NON_FIELD_ERRORS
from django.test.testcases import SimpleTestCase
from django.utils.encoding import force_text

from mtp_common.auth.forms import AuthenticationForm, PasswordChangeForm, ResetPasswordForm
from mtp_common.auth.models import MojUser


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

    def test_user_with_no_application_access(self, mocked_authenticate):
        """
        If the form restricts to a subset of applications,
        the user must have access to the same.
        This user has no application access.
        """
        mocked_authenticate.return_value = MojUser(1, 'abc', {})

        partial_form = functools.partial(AuthenticationForm, data=self.credentials)
        form = partial_form(restrict_applications=[])
        self.assertTrue(form.is_valid(),
                        msg='user with no app access should '
                            'be able to log in when unrestricted')
        self.assertEqual(form.errors.as_data(), {},
                         msg='user with no app access should '
                             'not see form errors if unrestricted')
        form = partial_form(restrict_applications=['app-1'])
        self.assertFalse(form.is_valid(),
                         msg='user with no app access should '
                             'not be able to log in if restricted')
        self.assertEqual(form.errors.as_data()[NON_FIELD_ERRORS][0].code, 'application_inaccessible',
                         msg='user with no app access should '
                             'see an error message if restricted')

    def test_user_with_access_to_one_app(self, mocked_authenticate):
        """
        If the form restricts to a subset of applications,
        the user must have access to the same.
        This user has access to one application.
        """
        mocked_authenticate.return_value = MojUser(1, 'abc', {'applications': ['app-1']})

        partial_form = functools.partial(AuthenticationForm, data=self.credentials)
        self.assertTrue(partial_form(restrict_applications=[]).is_valid(),
                        msg='user with access to one app should '
                            'be able to log in when unrestricted')
        self.assertTrue(partial_form(restrict_applications=['app-1']).is_valid(),
                        msg='user with access to one app should '
                            'be able to log in if restriction is met')
        self.assertFalse(partial_form(restrict_applications=['app-2']).is_valid(),
                         msg='user with access to one app should '
                             'not be able to log in if restriction not met')

    def test_user_with_access_to_several_apps(self, mocked_authenticate):
        """
        If the form restricts to a subset of applications,
        the user must have access to the same.
        This user has access to several applications.
        """
        mocked_authenticate.return_value = MojUser(1, 'abc', {'applications': ['app-2', 'app-3']})

        partial_form = functools.partial(AuthenticationForm, data=self.credentials)
        self.assertTrue(partial_form(restrict_applications=[]).is_valid(),
                        msg='user with access to several apps should '
                            'be able to log in when unrestricted')
        self.assertFalse(partial_form(restrict_applications=['app-1']).is_valid(),
                         msg='user with access to several apps should '
                             'not be able to log in if restriction is not met')
        self.assertTrue(partial_form(restrict_applications=['app-2']).is_valid(),
                        msg='user with access to several apps should '
                            'be able to log in if restriction is met')
        self.assertTrue(partial_form(restrict_applications=['app-2', 'app-3']).is_valid(),
                        msg='user with access to several apps should '
                            'be able to log in if all restrictions are met')
        self.assertFalse(partial_form(restrict_applications=['app-1', 'app-2', 'app-3']).is_valid(),
                         msg='user with access to several apps should '
                             'not be able to log in if some restrictions are not met')


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
        form = ResetPasswordForm(request=None, data={
            'username': 'admin'
        })
        self.assertTrue(form.is_valid())

        reset_password = mock_api_client.get_unauthenticated_connection().reset_password
        reset_password.post.assert_called_once_with({
            'username': 'admin'
        })
