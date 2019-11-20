import base64
import functools

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.utils.crypto import constant_time_compare


def basic_auth(user_setting, password_setting):
    def outer(view):
        @functools.wraps(view)
        def inner(request, *args, **kwargs):
            try:
                user = getattr(settings, user_setting)
                password = getattr(settings, password_setting)
            except AttributeError:
                raise ImproperlyConfigured(f'{user_setting} or {password_setting} Django settings are missing')

            if _check_basic_auth(request, user, password):
                response = view(request, *args, **kwargs)
            else:
                response = HttpResponse(status=401, content=b'Authentication required', content_type='text/plain')
                response['WWW-Authenticate'] = 'Basic realm="Authentication required"'
            return response

        return inner

    return outer


def _check_basic_auth(request, user, password):
    header = request.META.get('HTTP_AUTHORIZATION', '').split()
    if len(header) != 2 or header[0].lower() != 'basic':
        return False
    auth = header[1].encode()
    request_user, request_password = base64.b64decode(auth).split(b':')
    user_correct = constant_time_compare(user.encode(), request_user)
    password_correct = constant_time_compare(password.encode(), request_password)
    return user_correct and password_correct
