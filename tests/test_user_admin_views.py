import json
import logging
from unittest import mock

from django.conf import settings
from django.urls import reverse
import responses

from mtp_common.auth import login, urljoin
from mtp_common.auth.test_utils import generate_tokens
from mtp_common.test_utils import silence_logger
from .utils import SimpleTestCase


class UserAdminTestCase(SimpleTestCase):
    def mock_roles_list(self):
        responses.add(
            responses.GET,
            urljoin(settings.API_URL, '/roles/'),
            json={
                'count': 1,
                'results': [{
                    'name': 'prison-clerk',
                    'application': {
                        'name': 'Digital cashbook',
                        'client_id': 'cashbook',
                    }
                }],
            },
            status=200,
            content_type='application/json'
        )

    def mocked_login(self, **user_data_updates):
        with mock.patch('django.contrib.auth.login') as mock_login, \
                mock.patch('mtp_common.auth.backends.api_client') as mock_api_client:
            mock_login.side_effect = lambda request, user, *args: login(request, user)
            user_data = {
                'username': 'test-user',
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
                'token': generate_tokens(),
                'user_data': user_data,
            }
            self.assertTrue(self.client.login(username='test-user',
                                              password='blank'))


class UserListTestCase(UserAdminTestCase):

    @responses.activate
    def test_delete_user_permission_propagates(self):
        responses.add(
            responses.GET,
            urljoin(settings.API_URL, 'users'),
            json={'results': []},
            status=200,
            content_type='application/json'
        )
        self.mocked_login()
        response = self.client.get(reverse('list-users'))
        self.assertTrue(response.context['can_delete'])

    def test_admin_account_compatibility(self):
        self.mocked_login(roles=['prison-clerk', 'security'])
        response = self.client.get(reverse('list-users'))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-admin.html')


class DeleteUserTestCase(UserAdminTestCase):

    @responses.activate
    def test_user_not_found(self):
        responses.add(
            responses.DELETE,
            urljoin(settings.API_URL, '/users/test123/'),
            json={'detail': 'Not found'},
            status=404,
            content_type='application/json'
        )
        responses.add(
            responses.GET,
            urljoin(settings.API_URL, '/users'),
            json={'results': [], 'count': 0},
            status=200,
            content_type='application/json'
        )

        self.mocked_login()
        response = self.client.post(
            reverse('delete-user', kwargs={'username': 'test123'}), follow=True)
        messages = response.context['messages']
        messages = [str(m) for m in messages]
        self.assertIn('Not found', messages)

    @responses.activate
    def test_cannot_delete_self(self):
        responses.add(
            responses.DELETE,
            urljoin(settings.API_URL, '/users/test-user/'),
            json={'detail': 'You cannot disable yourself'},
            status=400,
            content_type='application/json'
        )
        responses.add(
            responses.GET,
            urljoin(settings.API_URL, '/users'),
            json={'results': [], 'count': 0},
            status=200,
            content_type='application/json'
        )

        self.mocked_login()
        response = self.client.post(
            reverse('delete-user', kwargs={'username': 'test-user'}), follow=True)
        messages = response.context['messages']
        messages = [str(m) for m in messages]
        self.assertIn('You cannot disable yourself', messages)


class NewUserTestCase(UserAdminTestCase):

    @responses.activate
    def test_new_user(self):
        new_user_data = {
            'username': 'new_user',
            'first_name': 'new',
            'last_name': 'user',
            'email': 'new@user.com',
            'user_admin': False,
            'role': 'prison-clerk',
        }

        responses.add(
            responses.POST,
            urljoin(settings.API_URL, 'users'),
            status=201,
            content_type='application/json'
        )

        self.mocked_login()
        self.mock_roles_list()
        with silence_logger('mtp', level=logging.WARNING):
            self.client.post(reverse('new-user'), data=new_user_data)

        self.assertEqual(
            json.loads(responses.calls[-1].request.body.decode('utf-8')),
            new_user_data
        )

    @responses.activate
    @mock.patch('tests.utils.get_template_source')
    def test_form_lists_roles(self, mocked_template):
        mocked_template.return_value = '{{ form }}'
        self.mocked_login()
        self.mock_roles_list()
        with silence_logger('mtp', level=logging.WARNING):
            response = self.client.get(reverse('new-user'))
        self.assertContains(response, 'Digital cashbook')
        self.assertSequenceEqual(
            response.context['form']['role'].field.choices,
            [('prison-clerk', 'Digital cashbook')]
        )

    @responses.activate
    def test_admin_account_compatibility(self):
        self.mocked_login(roles=['prison-clerk', 'security'])
        self.mock_roles_list()
        response = self.client.get(reverse('new-user'))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-admin.html')


class EditUserTestCase(UserAdminTestCase):
    def _init_existing_user(self, **user_data_edits):
        existing_user_data = {
            'username': 'current_user',
            'first_name': 'current',
            'last_name': 'user',
            'email': 'current@user.com',
            'user_admin': False,
            'roles': ['prison-clerk'],
        }
        existing_user_data.update(user_data_edits)
        responses.add(
            responses.GET,
            urljoin(settings.API_URL, '/users/current_user/'),
            json=existing_user_data,
            status=200,
            content_type='application/json'
        )

    @responses.activate
    def test_edit_user(self):
        self._init_existing_user()

        updated_user_data = {
            'first_name': 'dave',
            'last_name': 'smith',
            'email': 'current@user.com',
            'user_admin': True,
            'role': 'prison-clerk',
        }
        responses.add(
            responses.PATCH,
            urljoin(settings.API_URL, 'users/current_user/'),
            status=204,
            content_type='application/json'
        )

        self.mocked_login()
        self.mock_roles_list()
        with silence_logger('mtp', level=logging.WARNING):
            self.client.post(
                reverse('edit-user', kwargs={'username': 'current_user'}),
                data=updated_user_data
            )

        self.assertEqual(
            json.loads(responses.calls[-1].request.body.decode('utf-8')),
            updated_user_data
        )

    @responses.activate
    def test_cannot_change_username(self):
        self._init_existing_user()

        updated_user_data = {
            'username': 'new_user_name',
            'first_name': 'current',
            'last_name': 'user',
            'email': 'current@user.com',
            'user_admin': False,
            'role': 'prison-clerk',
        }
        responses.add(
            responses.PATCH,
            urljoin(settings.API_URL, 'users/current_user/'),
            status=204,
            content_type='application/json'
        )

        self.mocked_login()
        self.mock_roles_list()
        with silence_logger('mtp', level=logging.WARNING):
            self.client.post(
                reverse('edit-user', kwargs={'username': 'current_user'}),
                data=updated_user_data
            )

        del updated_user_data['username']

        self.assertEqual(
            json.loads(responses.calls[-1].request.body.decode('utf-8')),
            updated_user_data
        )

    @responses.activate
    @mock.patch('tests.utils.get_template_source')
    def test_editing_self_hides_roles_and_admin_status(self, mocked_template):
        mocked_template.return_value = '{{ form }}'
        self._init_existing_user(username='current_user')
        self.mocked_login(username='current_user')
        self.mock_roles_list()
        with silence_logger('mtp', level=logging.WARNING):
            response = self.client.get(reverse('edit-user', kwargs={'username': 'current_user'}))
        self.assertNotContains(response, 'Digital cashbook', msg_prefix=response.content.decode(response.charset))
        content = response.content.decode(response.charset)
        self.assertNotIn('user_admin', content)
        self.assertNotIn('role', content)

    @responses.activate
    def test_admin_account_compatibility(self):
        self._init_existing_user()
        self.mocked_login(roles=['prison-clerk', 'security'])
        self.mock_roles_list()
        response = self.client.get(reverse('edit-user', kwargs={'username': 'current_user'}))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-admin.html')

    @responses.activate
    def test_user_account_compatibility(self):
        self._init_existing_user(roles=['prison-clerk', 'security'])
        self.mocked_login()
        self.mock_roles_list()
        response = self.client.get(reverse('edit-user', kwargs={'username': 'current_user'}))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-user.html')
