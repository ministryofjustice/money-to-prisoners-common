from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver

from . import api_client, get_user_model

User = get_user_model()


class MojBackend(object):
    """
    Django authentication backend which authenticates against the api
    server using oauth2.

    Client Id and Secret can be changed in settings.
    """

    def authenticate(self, request, username=None, password=None):
        """
        Returns a valid `MojUser` if the authentication is successful
        or None if the credentials were wrong.
        """
        data = api_client.authenticate(username, password)
        if not data:
            return

        return User(
            data.get('pk'), data.get('token'), data.get('user_data')
        )

    def get_user(self, pk, token, user_data):
        return User(pk, token, user_data)


@receiver(user_logged_out)
def revoke_access_token(sender, **kwargs):
    try:
        user = kwargs['user']
        access_token = user.token['access_token']
    except (AttributeError, KeyError):
        return
    if access_token:
        api_client.revoke_token(access_token)
