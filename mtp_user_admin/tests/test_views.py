from unittest import mock

from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from slumber.exceptions import HttpClientError, HttpNotFoundError


@mock.patch('mtp_user_admin.views.api_client')
class DeleteUserTestCase(SimpleTestCase):

    def test_user_not_found(self, mock_api_client):
        conn = mock_api_client.get_connection()
        conn.users.get.return_value = {}
        conn.users().delete.side_effect = HttpNotFoundError(content=b'{"detail": "Not found"}')

        self.client.login(username='test-user')
        response = self.client.post(reverse('delete-user', args={'username': 'test123'}),
                                    follow=True)
        messages = response.context['messages']
        messages = [str(m) for m in messages]
        self.assertIn('Not found', messages)

    def test_cannot_delete_self(self, mock_api_client):
        conn = mock_api_client.get_connection()
        conn.users.get.return_value = {}
        conn.users().delete.side_effect = HttpClientError(content=b'{"__all__": ["You cannot delete yourself"]}')

        self.client.login(username='test-user')
        response = self.client.post(reverse('delete-user', args={'username': 'test-user'}),
                                    follow=True)
        messages = response.context['messages']
        messages = [str(m) for m in messages]
        self.assertIn('You cannot delete yourself', messages)


@mock.patch('mtp_user_admin.forms.api_client')
class NewUserTestCase(SimpleTestCase):

    def test_new_user(self, mock_api_client):
        new_user_data = {
            'username': 'new_user',
            'first_name': 'new',
            'last_name': 'user',
            'email': 'new@user.com',
            'user_admin': False,
        }
        self.client.login(username='test-user')
        self.client.post(reverse('new-user'), data=new_user_data)

        mock_api_client.get_connection().users().post.assert_called_with(new_user_data)


@mock.patch('mtp_user_admin.forms.api_client')
@mock.patch('mtp_user_admin.views.api_client')
class EditUserTestCase(SimpleTestCase):

    def _init_existing_user(self, mock_form_api_client):
        existing_user_data = {
            'username': 'current_user',
            'first_name': 'current',
            'last_name': 'user',
            'email': 'current@user.com',
            'user_admin': False,
        }
        conn = mock_form_api_client.get_connection()
        conn.users().get.return_value = existing_user_data

    def test_edit_user(self, mock_view_api_client, mock_form_api_client):
        self._init_existing_user(mock_form_api_client)

        updated_user_data = {
            'first_name': 'dave',
            'last_name': 'smith',
            'email': 'current@user.com',
            'user_admin': True,
        }
        self.client.login(username='test-user')
        self.client.post(
            reverse('edit-user', args={'username': 'current_user'}),
            data=updated_user_data
        )

        conn = mock_form_api_client.get_connection()
        conn.users().patch.assert_called_with(updated_user_data)

    def test_cannot_change_username(self, mock_view_api_client, mock_form_api_client):
        self._init_existing_user(mock_form_api_client)

        updated_user_data = {
            'username': 'new_user_name',
            'first_name': 'current',
            'last_name': 'user',
            'email': 'current@user.com',
            'user_admin': False,
        }
        self.client.login(username='test-user')
        self.client.post(
            reverse('edit-user', args={'username': 'current_user'}),
            data=updated_user_data
        )

        del updated_user_data['username']

        conn = mock_form_api_client.get_connection()
        conn.users().patch.assert_called_with(updated_user_data)
