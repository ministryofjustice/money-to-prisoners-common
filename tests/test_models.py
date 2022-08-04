from django.test import SimpleTestCase

from mtp_common.auth.models import MojUser, MojAnonymousUser
from mtp_common.auth.test_utils import generate_tokens


class UserPermissionsTestCase(SimpleTestCase):
    def setUp(self):
        self.user = MojUser(5, generate_tokens(), {
            'pk': 5,
            'username': 'sam-hall',
            'first_name': 'Sam',
            'last_name': 'Hall',
            'email': 'sam@mtp.local',
            'permissions': [
                'allowed_permission_1',
                'allowed_permission_2',
                'allowed_permission_3'
            ],
        })

    def test_fields(self):
        self.assertEqual(self.user.get_username(), 'sam-hall')
        self.assertEqual(self.user.first_name, 'Sam')
        self.assertEqual(self.user.last_name, 'Hall')
        self.assertEqual(self.user.get_full_name(), 'Sam Hall')
        self.assertEqual(self.user.get_short_name(), 'Sam')
        self.assertEqual(self.user.email, 'sam@mtp.local')

    def test_has_perm_succeeds_if_present(self):
        self.assertTrue(self.user.has_perm('allowed_permission_1'))

    def test_has_perm_fails_if_absent(self):
        self.assertFalse(self.user.has_perm('forbidden_permission'))

    def test_has_perms_succeeds_if_all_present(self):
        self.assertTrue(self.user.has_perms([
            'allowed_permission_1',
            'allowed_permission_2'
        ]))

    def test_has_perms_fails_if_any_absent(self):
        self.assertFalse(self.user.has_perms([
            'allowed_permission_1',
            'forbidden_permission'
        ]))

    def test_no_permissions_fails_gracefully(self):
        user = MojUser(6, generate_tokens(), {
            'first_name': 'Sam',
            'last_name': 'Halle',
        })

        user.get_all_permissions()
        self.assertFalse(user.has_perm('forbidden_permission'))
        self.assertFalse(user.has_perms([
            'allowed_permission_1',
            'forbidden_permission'
        ]))


class AnonymousUserPermissionsTestCase(SimpleTestCase):
    def setUp(self):
        self.user = MojAnonymousUser()

    def test_fields(self):
        self.assertEqual(self.user.get_username(), '')
        self.assertEqual(self.user.first_name, '')
        self.assertEqual(self.user.last_name, '')
        self.assertEqual(self.user.get_full_name(), '')
        self.assertEqual(self.user.get_short_name(), '')
        self.assertEqual(self.user.email, '')

    def test_has_no_perms(self):
        self.assertFalse(self.user.has_perm('change_something'))
