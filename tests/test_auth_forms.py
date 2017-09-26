import json
from unittest import mock

from django.conf import settings
from django.test.testcases import SimpleTestCase
from django.utils.encoding import force_text
import responses

from mtp_common.auth import urljoin
from mtp_common.auth.forms import (
    AuthenticationForm, PasswordChangeForm, ResetPasswordForm, RESET_CODE_PARAM
)
from mtp_common.auth.test_utils import generate_tokens


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


class PasswordChangeFormTestCase(SimpleTestCase):

    def setUp(self):
        super().setUp()
        self.request = mock.MagicMock(
            user=mock.MagicMock(
                token=generate_tokens()
            )
        )

    @responses.activate
    def test_change_password(self):
        responses.add(
            responses.POST,
            urljoin(settings.API_URL, 'change_password'),
            status=204,
            content_type='application/json'
        )

        form = PasswordChangeForm(
            self.request,
            data={
                'old_password': 'old',
                'new_password': 'new',
                'new_password_confirmation': 'new'
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(
            json.loads(responses.calls[0].request.body.decode('utf-8')),
            {'old_password': 'old', 'new_password': 'new'}
        )

    def test_non_matching_new_passwords_fail(self):
        form = PasswordChangeForm(
            self.request,
            data={
                'old_password': 'old',
                'new_password': 'new1',
                'new_password_confirmation': 'new2'
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(len(responses.calls), 0)


class ResetPasswordFormTestCase(SimpleTestCase):

    @responses.activate
    def test_reset_password(self):
        responses.add(
            responses.POST,
            urljoin(settings.API_URL, 'reset_password'),
            status=204,
            content_type='application/json'
        )

        password_change_url = '/change_password'
        form = ResetPasswordForm(password_change_url=password_change_url, request=None, data={
            'username': 'admin'
        })
        self.assertTrue(form.is_valid())

        self.assertEqual(
            json.loads(responses.calls[0].request.body.decode('utf-8')),
            {
                'username': 'admin',
                'create_password': {
                    'password_change_url': settings.SITE_URL + password_change_url,
                    'reset_code_param': RESET_CODE_PARAM
                }
            }
        )
