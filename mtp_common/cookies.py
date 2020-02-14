import functools
from http.cookies import Morsel

import django
from django.conf import settings
from django.http.response import HttpResponseBase
from django.utils.deprecation import MiddlewareMixin


def patch_samesite_cookies():
    version = django.get_version()
    version = version.split('.', 2)[:2]
    if version >= ['2', '1']:
        # django2.1+ supports samesite cookies
        return

    Morsel._reserved['samesite'] = 'SameSite'
    base_set_cookie = HttpResponseBase.set_cookie

    @functools.wraps(base_set_cookie)
    def set_cookie(
        self, key, value='',
        max_age=None, expires=None, path='/', domain=None, secure=False, httponly=False, samesite=None
    ):
        base_set_cookie(
            self, key, value=value,
            max_age=max_age, expires=expires, path=path, domain=domain, secure=secure, httponly=httponly,
        )
        if samesite:
            if samesite not in ('Strict', 'Lax', 'None'):
                raise ValueError('Invalid samesite')
            self.cookies[key]['samesite'] = samesite

    HttpResponseBase.set_cookie = set_cookie

    settings.MIDDLEWARE = list(settings.MIDDLEWARE)
    settings.MIDDLEWARE.append('mtp_common.cookies.SameSiteMiddleware')


class SameSiteMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        flags = {
            settings.SESSION_COOKIE_NAME: getattr(settings, 'SESSION_COOKIE_SAMESITE', None),
            settings.CSRF_COOKIE_NAME: getattr(settings, 'CSRF_COOKIE_SAMESITE', None),
        }
        for cookie, flag in flags.items():
            if flag:
                response.cookies[cookie]['samesite'] = flag
        return response
