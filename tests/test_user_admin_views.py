import logging
from unittest import mock

from django.core.urlresolvers import reverse
from slumber.exceptions import HttpClientError, HttpNotFoundError

from mtp_common.auth import login
from mtp_common.test_utils import silence_logger
from .utils import SimpleTestCase


class UserAdminTestCase(SimpleTestCase):
    def mock_roles_list(self, mock_api_client):
        mock_api_client.get_connection().roles.get.return_value = {
            'count': 1,
            'results': [{
                'name': 'prison-clerk',
                'application': {
                    'name': 'Digital cashbook',
                    'client_id': 'cashbook',
                }
            }],
        }

    def mocked_login(self, **user_data_updates):
        with mock.patch('django.contrib.auth.login') as mock_login, \
                mock.patch('mtp_common.auth.backends.api_client') as mock_api_client:
            mock_login.side_effect = lambda request, user, *args: login(request, user)
            user_data = {
                'username': 'test',
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@mtp.local',
                'permissions': [
                    'auth.add_user', 'auth.change_user', 'auth.delete_user',
                ],
                'prisons': [{'nomis_id': 'AAI', 'name': 'Prison 1', 'pre_approval_required': False}],
                'roles': ['prison-clerk'],
            }
            user_data.update(user_data_updates)
            mock_api_client.authenticate.return_value = {
                'pk': 1,
                'token': 'xxx',
                'user_data': user_data,
            }
            self.assertTrue(self.client.login(username='test-user',
                                              password='blank'))


class UserListTestCase(UserAdminTestCase):
    @mock.patch('mtp_common.user_admin.views.api_client')
    def test_delete_user_permission_propagates(self, mock_api_client):
        conn = mock_api_client.get_connection()
        conn.users.get.return_value = {'results': []}
        self.mocked_login()
        response = self.client.get(reverse('list-users'))
        self.assertTrue(response.context['can_delete'])

    def test_admin_account_compatibility(self):
        self.mocked_login(roles=['prison-clerk', 'security'])
        response = self.client.get(reverse('list-users'))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-admin.html')


@mock.patch('mtp_common.user_admin.views.api_client')
class DeleteUserTestCase(UserAdminTestCase):
    def test_user_not_found(self, mock_api_client):
        conn = mock_api_client.get_connection()
        conn.users.get.return_value = {}
        conn.users().delete.side_effect = HttpNotFoundError(content=b'{"detail": "Not found"}')

        self.mocked_login()
        response = self.client.post(reverse('delete-user', args={'username': 'test123'}),
                                    follow=True)
        messages = response.context['messages']
        messages = [str(m) for m in messages]
        self.assertIn('Not found', messages)

    def test_cannot_delete_self(self, mock_api_client):
        conn = mock_api_client.get_connection()
        conn.users.get.return_value = {}
        conn.users().delete.side_effect = HttpClientError(content=b'{"__all__": ["You cannot disable yourself"]}')

        self.mocked_login()
        response = self.client.post(reverse('delete-user', args={'username': 'test-user'}),
                                    follow=True)
        messages = response.context['messages']
        messages = [str(m) for m in messages]
        self.assertIn('You cannot disable yourself', messages)


@mock.patch('mtp_common.user_admin.forms.api_client')
class NewUserTestCase(UserAdminTestCase):
    def test_new_user(self, mock_api_client):
        new_user_data = {
            'username': 'new_user',
            'first_name': 'new',
            'last_name': 'user',
            'email': 'new@user.com',
            'user_admin': False,
            'role': 'prison-clerk',
        }
        self.mocked_login()
        self.mock_roles_list(mock_api_client)
        with silence_logger('mtp', level=logging.WARNING):
            self.client.post(reverse('new-user'), data=new_user_data)

        mock_api_client.get_connection().users().post.assert_called_with(new_user_data)

    @mock.patch('tests.utils.get_template_source')
    def test_form_lists_roles(self, mocked_template, mock_api_client):
        mocked_template.return_value = '{{ form }}'
        self.mocked_login()
        self.mock_roles_list(mock_api_client)
        with silence_logger('mtp', level=logging.WARNING):
            response = self.client.get(reverse('new-user'))
        self.assertContains(response, 'Digital cashbook')
        self.assertSequenceEqual(
            response.context['form']['role'].field.choices,
            [('prison-clerk', 'Digital cashbook')]
        )

    def test_admin_account_compatibility(self, mock_api_client):
        self.mocked_login(roles=['prison-clerk', 'security'])
        self.mock_roles_list(mock_api_client)
        response = self.client.get(reverse('new-user'))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-admin.html')


@mock.patch('mtp_common.user_admin.forms.api_client')
@mock.patch('mtp_common.user_admin.views.api_client')
class EditUserTestCase(UserAdminTestCase):
    def _init_existing_user(self, *api_client_mocks, **user_data_edits):
        existing_user_data = {
            'username': 'current_user',
            'first_name': 'current',
            'last_name': 'user',
            'email': 'current@user.com',
            'user_admin': False,
            'roles': ['prison-clerk'],
        }
        existing_user_data.update(user_data_edits)
        for api_client_mock in api_client_mocks:
            connection = api_client_mock.get_connection()
            connection.users().get.return_value = existing_user_data

    def test_edit_user(self, mock_view_api_client, mock_form_api_client):
        self._init_existing_user(mock_view_api_client, mock_form_api_client)

        updated_user_data = {
            'first_name': 'dave',
            'last_name': 'smith',
            'email': 'current@user.com',
            'user_admin': True,
            'role': 'prison-clerk',
        }
        self.mocked_login()
        self.mock_roles_list(mock_form_api_client)
        with silence_logger('mtp', level=logging.WARNING):
            self.client.post(
                reverse('edit-user', args={'username': 'dave'}),
                data=updated_user_data
            )

        conn = mock_form_api_client.get_connection()
        conn.users().patch.assert_called_with(updated_user_data)

    def test_cannot_change_username(self, mock_view_api_client, mock_form_api_client):
        self._init_existing_user(mock_view_api_client, mock_form_api_client)

        updated_user_data = {
            'username': 'new_user_name',
            'first_name': 'current',
            'last_name': 'user',
            'email': 'current@user.com',
            'user_admin': False,
            'role': 'prison-clerk',
        }
        self.mocked_login()
        self.mock_roles_list(mock_form_api_client)
        with silence_logger('mtp', level=logging.WARNING):
            self.client.post(
                reverse('edit-user', args={'username': 'current_user'}),
                data=updated_user_data
            )

        del updated_user_data['username']

        conn = mock_form_api_client.get_connection()
        conn.users().patch.assert_called_with(updated_user_data)

    @mock.patch('tests.utils.get_template_source')
    def test_editing_self_hides_roles_and_admin_status(self, mocked_template,
                                                       mock_view_api_client, mock_form_api_client):
        mocked_template.return_value = '{{ form }}'
        self._init_existing_user(mock_view_api_client, mock_form_api_client, username='test')
        self.mocked_login()
        self.mock_roles_list(mock_form_api_client)
        with silence_logger('mtp', level=logging.WARNING):
            response = self.client.get(reverse('edit-user', args={'username': 'current_user'}))
        self.assertNotContains(response, 'Digital cashbook', msg_prefix=response.content.decode(response.charset))
        content = response.content.decode(response.charset)
        self.assertNotIn('user_admin', content)
        self.assertNotIn('role', content)

    def test_admin_account_compatibility(self, mock_view_api_client, mock_form_api_client):
        self._init_existing_user(mock_view_api_client, mock_form_api_client)
        self.mocked_login(roles=['prison-clerk', 'security'])
        self.mock_roles_list(mock_form_api_client)
        response = self.client.get(reverse('edit-user', args={'username': 'current_user'}))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-admin.html')

    def test_user_account_compatibility(self, mock_view_api_client, mock_form_api_client):
        self._init_existing_user(mock_view_api_client, mock_form_api_client, roles=['prison-clerk', 'security'])
        self.mocked_login()
        self.mock_roles_list(mock_form_api_client)
        response = self.client.get(reverse('edit-user', args={'username': 'dave'}))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-user.html')
