from unittest import mock


def create_mock_user():
    user = mock.Mock()
    user.backend = TestBackend
    user.is_active = True
    user._meta.pk.value_to_string.return_value = '1'
    user.get_session_auth_hash.return_value = 'xxx'
    return user


class TestBackend(object):

    def authenticate(self, username=None, password=None):
        return create_mock_user()

    def get_user(self, user_id):
        return create_mock_user()
