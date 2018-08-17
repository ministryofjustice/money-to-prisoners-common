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
    def mock_roles_list(self, rsps):
        rsps.add(
            rsps.GET,
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
    def test_list_users(self):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'users'),
                json={'results': [
                    {
                        'first_name': 'John', 'last_name': 'Smith',
                        'username': 'john123', 'email': 'john@mtp.local',
                        'is_active': True, 'is_locked_out': False, 'user_admin': False,
                    },
                    {
                        'first_name': 'Mary', 'last_name': 'Marks',
                        'username': 'mary321', 'email': 'mary@mtp.local',
                        'is_active': False, 'is_locked_out': False, 'user_admin': True,
                    },
                ], 'count': 2},
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'requests'),
                json={'results': [], 'count': 0},
                content_type='application/json'
            )
            response = self.client.get(reverse('list-users'))
        self.assertNotContains(response, 'New user requests')
        self.assertContains(response, 'Edit existing users')
        content = response.content.decode(response.charset)
        self.assertIn('john123', content)
        self.assertIn('mary321', content)
        self.assertIn('User can manage other accounts', content)

    def test_delete_user_permission_propagates(self):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'users'),
                json={'results': []},
                status=200,
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'requests'),
                json={'results': [], 'count': 0},
                content_type='application/json'
            )
            response = self.client.get(reverse('list-users'))
        self.assertTrue(response.context['can_delete'])

    def test_admin_account_compatibility(self):
        self.mocked_login(roles=['prison-clerk', 'security'])
        with responses.RequestsMock():
            response = self.client.get(reverse('list-users'))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-admin.html')

    def test_list_account_requests(self):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'users'),
                json={'results': [], 'count': 0},
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'requests'),
                json={'results': [
                    {
                        'created': '2018-08-12T12:00:00Z', 'id': 1,
                        'first_name': 'John', 'last_name': 'Smith',
                        'username': 'john123', 'email': 'john@mtp.local',
                    },
                    {
                        'created': '2018-08-13T12:10:00Z', 'id': 2,
                        'first_name': 'Mary', 'last_name': 'Marks',
                        'username': 'mary321', 'email': 'mary@mtp.local',
                    },
                ], 'count': 2},
                content_type='application/json'
            )
            response = self.client.get(reverse('list-users'))
        self.assertContains(response, 'New user requests')
        self.assertContains(response, 'Edit existing users')
        content = response.content.decode(response.charset)
        self.assertIn('John Smith', content)
        self.assertIn('Mary Marks', content)
        self.assertIn('12/08/2018', content)
        self.assertNotIn('john123', content)


class DeleteUserTestCase(UserAdminTestCase):
    def test_user_not_found(self):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.DELETE,
                urljoin(settings.API_URL, '/users/test123/'),
                json={'detail': 'Not found'},
                status=404,
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, '/users'),
                json={'results': [], 'count': 0},
                status=200,
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'requests'),
                json={'results': [], 'count': 0},
                content_type='application/json'
            )

            response = self.client.post(
                reverse('delete-user', kwargs={'username': 'test123'}), follow=True)
        messages = response.context['messages']
        messages = [str(m) for m in messages]
        self.assertIn('Not found', messages)

    def test_cannot_delete_self(self):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.DELETE,
                urljoin(settings.API_URL, '/users/test-user/'),
                json={'detail': 'You cannot disable yourself'},
                status=400,
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, '/users'),
                json={'results': [], 'count': 0},
                status=200,
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'requests'),
                json={'results': [], 'count': 0},
                content_type='application/json'
            )

            response = self.client.post(
                reverse('delete-user', kwargs={'username': 'test-user'}), follow=True)
        messages = response.context['messages']
        messages = [str(m) for m in messages]
        self.assertIn('You cannot disable yourself', messages)


class NewUserTestCase(UserAdminTestCase):
    def test_new_user(self):
        self.mocked_login()
        new_user_data = {
            'username': 'new_user',
            'first_name': 'new',
            'last_name': 'user',
            'email': 'new@user.com',
            'user_admin': False,
            'role': 'prison-clerk',
        }
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                urljoin(settings.API_URL, 'users'),
                status=201,
                content_type='application/json'
            )

            self.mock_roles_list(rsps)
            with silence_logger('mtp', level=logging.WARNING):
                self.client.post(reverse('new-user'), data=new_user_data)

            self.assertEqual(
                json.loads(rsps.calls[-1].request.body.decode()),
                new_user_data
            )

    @mock.patch('tests.urls.mocked_template')
    def test_form_lists_roles(self, mocked_template):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            mocked_template.return_value = '{{ form }}'
            self.mock_roles_list(rsps)
            with silence_logger('mtp', level=logging.WARNING):
                response = self.client.get(reverse('new-user'))
        self.assertContains(response, 'prison-clerk')
        self.assertSequenceEqual(
            response.context['form']['role'].field.choices,
            [('prison-clerk', 'Digital cashbook')]
        )

    def test_admin_account_compatibility(self):
        self.mocked_login(roles=['prison-clerk', 'security'])
        with responses.RequestsMock():
            response = self.client.get(reverse('new-user'))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-admin.html')


class EditUserTestCase(UserAdminTestCase):
    def _init_existing_user(self, rsps, **user_data_edits):
        existing_user_data = {
            'username': 'current_user',
            'first_name': 'current',
            'last_name': 'user',
            'email': 'current@user.com',
            'user_admin': False,
            'roles': ['prison-clerk'],
        }
        existing_user_data.update(user_data_edits)
        rsps.add(
            rsps.GET,
            urljoin(settings.API_URL, '/users/current_user/'),
            json=existing_user_data,
            status=200,
            content_type='application/json'
        )

    def test_edit_user(self):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            self._init_existing_user(rsps)
            self.mock_roles_list(rsps)

            response = self.client.get(reverse('edit-user', kwargs={'username': 'current_user'}))
            content = response.content.decode(response.charset)
            self.assertIn('id_user_admin', content)
            self.assertNotIn('id_role', content)

            updated_user_data = {
                'first_name': 'dave',
                'last_name': 'smith',
                'email': 'current@user.com',
                'user_admin': True,
                'role': 'prison-clerk',
            }

            rsps.add(
                rsps.PATCH,
                urljoin(settings.API_URL, 'users/current_user/'),
                status=204,
                content_type='application/json'
            )
            with silence_logger('mtp', level=logging.WARNING):
                self.client.post(
                    reverse('edit-user', kwargs={'username': 'current_user'}),
                    data=updated_user_data
                )

            self.assertEqual(
                json.loads(rsps.calls[-1].request.body.decode()),
                updated_user_data
            )

    def test_cannot_change_username(self):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            self._init_existing_user(rsps)

            updated_user_data = {
                'username': 'new_user_name',
                'first_name': 'current',
                'last_name': 'user',
                'email': 'current@user.com',
                'user_admin': False,
                'role': 'prison-clerk',
            }
            rsps.add(
                rsps.PATCH,
                urljoin(settings.API_URL, 'users/current_user/'),
                status=204,
                content_type='application/json'
            )

            self.mock_roles_list(rsps)
            with silence_logger('mtp', level=logging.WARNING):
                self.client.post(
                    reverse('edit-user', kwargs={'username': 'current_user'}),
                    data=updated_user_data
                )

            del updated_user_data['username']

            self.assertEqual(
                json.loads(rsps.calls[-1].request.body.decode()),
                updated_user_data
            )

    def test_editing_self_hides_roles_and_admin_status(self):
        self.mocked_login(username='current_user')
        with responses.RequestsMock() as rsps:
            self._init_existing_user(rsps, username='current_user')
            with silence_logger('mtp', level=logging.WARNING):
                response = self.client.get(reverse('edit-user', kwargs={'username': 'current_user'}))
        self.assertNotContains(response, 'Digital cashbook', msg_prefix=response.content.decode(response.charset))
        content = response.content.decode(response.charset)
        self.assertNotIn('id_user_admin', content)
        self.assertNotIn('id_role', content)

    def test_admin_account_compatibility(self):
        self.mocked_login(roles=['prison-clerk', 'security'])
        with responses.RequestsMock():
            response = self.client.get(reverse('edit-user', kwargs={'username': 'current_user'}))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-admin.html')

    def test_user_account_compatibility(self):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            self._init_existing_user(rsps, roles=['prison-clerk', 'security'])
            response = self.client.get(reverse('edit-user', kwargs={'username': 'current_user'}))
        self.assertEqual(response.templates[0].name, 'mtp_common/user_admin/incompatible-user.html')


class SignUpTestCase(SimpleTestCase):
    def test_sign_up(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST, urljoin(settings.API_URL, '/requests/'),
                json={}, status=201,
                content_type='application/json'
            )
            response = self.client.post(reverse('sign-up'), data={
                'first_name': 'A', 'last_name': 'B',
                'email': 'a@mtp.local', 'username': 'abc',
                'role': 'general',
            })
        self.assertContains(response, 'Your request for access has been sent')

    def test_missing_fields(self):
        with responses.RequestsMock():
            response = self.client.post(reverse('sign-up'), data={
                'first_name': 'A', 'last_name': '',
                'email': 'a@mtp.local', 'username': 'abc',
                'role': 'general',
            })
        self.assertNotContains(response, 'Your request for access has been sent')
        self.assertContains(response, 'field is required')

    def test_api_error_response(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST, urljoin(settings.API_URL, '/requests/'),
                json={'non_field_errors': 'Duplicate request'}, status=400,
                content_type='application/json'
            )
            response = self.client.post(reverse('sign-up'), data={
                'first_name': 'A', 'last_name': 'B',
                'email': 'a@mtp.local', 'username': 'abc',
                'role': 'general',
            })
        self.assertNotContains(response, 'Your request for access has been sent')
        self.assertContains(response, 'Duplicate request')

    def test_unexpected_api_error_response(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST, urljoin(settings.API_URL, '/requests/'),
                json={'abc': '******'}, status=400,
                content_type='application/json'
            )
            with silence_logger('mtp'):
                response = self.client.post(reverse('sign-up'), data={
                    'first_name': 'A', 'last_name': 'B',
                    'email': 'a@mtp.local', 'username': 'abc',
                    'role': 'general',
                })
        self.assertNotContains(response, 'Your request for access has been sent')
        self.assertNotContains(response, '******')
        self.assertContains(response, 'This service is currently unavailable')

    def test_shows_has_role_page(self):
        with responses.RequestsMock() as rsps:
            error = {
                'condition': 'user-exists',
                'roles': [{'role': 'general',
                           'application': 'Application 1',
                           'login_url': 'http://example.com/1'}],
            }
            rsps.add(
                rsps.POST, urljoin(settings.API_URL, '/requests/'),
                json={'__mtp__': error, 'username': 'Exists'}, status=400,
                content_type='application/json'
            )
            response = self.client.post(reverse('sign-up'), data={
                'first_name': 'A', 'last_name': 'B',
                'email': 'a@mtp.local', 'username': 'abc',
                'role': 'general',
            })
        self.assertContains(response, 'You already have access to this service')
        self.assertContains(response, 'http://example.com/1')

    def test_shows_has_other_roles_page(self):
        with responses.RequestsMock() as rsps:
            error = {
                'condition': 'user-exists',
                'roles': [{'role': 'general',
                           'application': 'Application 1',
                           'login_url': 'http://example.com/1'}],
            }
            rsps.add(
                rsps.POST, urljoin(settings.API_URL, '/requests/'),
                json={'__mtp__': error, 'username': 'Exists'}, status=400,
                content_type='application/json'
            )
            response = self.client.post(reverse('sign-up'), data={
                'first_name': 'A', 'last_name': 'B',
                'email': 'a@mtp.local', 'username': 'abc',
                'role': 'special',
            })
        self.assertContains(response, 'You will lose access to this service')
        self.assertContains(response, 'Application 1')
        self.assertContains(response, 'http://example.com/1')


class AccountRequestTestCase(UserAdminTestCase):
    def assertAcceptRequest(self, user_admin):  # noqa: N802
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'requests', '1'),
                json={
                    'created': '2018-08-12T12:00:00Z', 'id': 1,
                    'first_name': 'A', 'last_name': 'B',
                    'email': 'a@mtp.local', 'username': 'abc',
                    'role': 'general', 'reason': ''
                },
                content_type='application/json'
            )
            response = self.client.get(reverse('accept-request', kwargs={'account_request': 1}))

            self.assertContains(response, 'New user request')
            content = response.content.decode(response.charset)
            self.assertIn('A B', content)
            self.assertIn('12/08/2018', content)
            self.assertIn('a@mtp.local', content)
            self.assertIn('abc', content)
            self.assertNotIn('Reason', content)

            rsps.add(
                rsps.PATCH,
                urljoin(settings.API_URL, 'requests', '1'),
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'users'),
                json={'results': [], 'count': 0},
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'requests'),
                json={'results': [], 'count': 0},
                content_type='application/json'
            )
            payload = {}
            if user_admin:
                payload['user_admin'] = 'on'
            response = self.client.post(reverse('accept-request', kwargs={'account_request': 1}),
                                        data=payload, follow=True)

            self.assertContains(response, 'New user request accepted')
            patch_call = rsps.calls[-3]
            if user_admin:
                self.assertEqual(patch_call.request.body, 'user_admin=True')
            else:
                self.assertEqual(patch_call.request.body, 'user_admin=False')

    def test_accept_account_requests(self):
        self.mocked_login()
        self.assertAcceptRequest(user_admin=False)
        self.assertAcceptRequest(user_admin=True)

    def test_decline_account_requests(self):
        self.mocked_login()
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.DELETE,
                urljoin(settings.API_URL, 'requests', '1'),
                status=204,
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'users'),
                json={'results': [], 'count': 0},
                content_type='application/json'
            )
            rsps.add(
                rsps.GET,
                urljoin(settings.API_URL, 'requests'),
                json={'results': [], 'count': 0},
                content_type='application/json'
            )
            response = self.client.post(reverse('decline-request', kwargs={'account_request': 1}), follow=True)
            self.assertContains(response, 'New user request was declined')
