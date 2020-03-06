from django.urls import reverse

from tests.test_auth_views import AuthenticatedTestCase


class SettingsViewTestCase(AuthenticatedTestCase):
    def test_login_required_to_view(self):
        response = self.client.get(reverse('settings'), follow=True)
        self.assertNotContains(response, 'Change your password')

    def test_can_view_settings_if_authenticated(self):
        self.login()
        response = self.client.get(reverse('settings'), follow=True)
        self.assertContains(response, 'Change your password')
