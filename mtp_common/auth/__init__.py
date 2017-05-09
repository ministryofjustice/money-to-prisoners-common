from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import load_backend
from django.middleware.csrf import rotate_token
from django.utils.crypto import constant_time_compare
from django.utils.module_loading import import_string
from django.utils.translation import LANGUAGE_SESSION_KEY

from .models import MojAnonymousUser, MojUser

SESSION_KEY = '_auth_user_id'
AUTH_TOKEN_SESSION_KEY = '_auth_user_auth_token'
USER_DATA_SESSION_KEY = '_auth_user_data'
BACKEND_SESSION_KEY = '_auth_user_backend'
HASH_SESSION_KEY = '_auth_user_hash'


def update_token_in_session(session, token):
    session[AUTH_TOKEN_SESSION_KEY] = token


def login(request, user):
    """
    Persist a user id and a backend in the request. This way a user doesn't
    have to reauthenticate on every request. Note that data set during
    the anonymous session is retained when the user logs in.
    """
    session_auth_hash = ''
    if user is None:
        user = request.user
    if hasattr(user, 'get_session_auth_hash'):
        session_auth_hash = user.get_session_auth_hash()

    if SESSION_KEY in request.session:
        session_key = request.session[SESSION_KEY]
        if session_key != user.pk or (
                session_auth_hash and
                request.session.get(HASH_SESSION_KEY) != session_auth_hash):
            # To avoid reusing another user's session, create a new, empty
            # session if the existing session corresponds to a different
            # authenticated user.
            request.session.flush()
    else:
        request.session.cycle_key()
    request.session[SESSION_KEY] = user.pk
    request.session[BACKEND_SESSION_KEY] = user.backend
    request.session[USER_DATA_SESSION_KEY] = user.user_data
    request.session[HASH_SESSION_KEY] = session_auth_hash

    update_token_in_session(request.session, user.token)

    if hasattr(request, 'user'):
        request.user = user
    rotate_token(request)
    user_logged_in.send(sender=user.__class__, request=request, user=user)


def get_user(request):
    """
    Returns the user model instance associated with the given request session.
    If no user is retrieved an instance of `MojAnonymousUser` is returned.
    """
    user = None
    try:
        user_id = request.session[SESSION_KEY]
        token = request.session[AUTH_TOKEN_SESSION_KEY]
        user_data = request.session[USER_DATA_SESSION_KEY]
        backend_path = request.session[BACKEND_SESSION_KEY]
    except KeyError:
        pass
    else:
        if backend_path in settings.AUTHENTICATION_BACKENDS:
            backend = load_backend(backend_path)
            user = backend.get_user(user_id, token, user_data)
            # Verify the session
            if hasattr(user, 'get_session_auth_hash'):
                session_hash = request.session.get(HASH_SESSION_KEY)
                session_hash_verified = session_hash and constant_time_compare(
                    session_hash,
                    user.get_session_auth_hash()
                )
                if not session_hash_verified:
                    request.session.flush()
                    user = None

    return user or MojAnonymousUser()


def get_user_model():
    try:
        return import_string(settings.MOJ_USER_MODEL)
    except AttributeError:
        return MojUser


def logout(request):
    """
    Removes the authenticated user's ID from the request and flushes their
    session data.
    """
    # Dispatch the signal before the user is logged out so the receivers have a
    # chance to find out *who* logged out.
    user = getattr(request, 'user', None)
    if hasattr(user, 'is_authenticated') and not user.is_authenticated():
        user = None
    user_logged_out.send(sender=user.__class__, request=request, user=user)

    # remember language choice saved to session
    language = request.session.get(LANGUAGE_SESSION_KEY)

    request.session.flush()

    if language is not None:
        request.session[LANGUAGE_SESSION_KEY] = language

    if hasattr(request, 'user'):
        request.user = MojAnonymousUser()


def urljoin(base, *parts):
    return '/'.join([s.strip('/') for s in [base] + list(parts)]) + '/'
