from unittest import mock

from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from slumber.exceptions import HttpNotFoundError


@mock.patch('mtp_user_admin.views.api_client')
class DeleteUserTestCase(SimpleTestCase):

    def test_user_not_found_raises_404(self, mock_api_client):
        conn = mock_api_client.get_connection()
        conn.users().delete.side_effect = HttpNotFoundError()

        self.client.login(username='test-user')
        response = self.client.post(reverse('delete-user', args={'username': 'test123'}))
        self.assertEqual(response.status_code, 404)
