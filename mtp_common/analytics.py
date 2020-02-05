import datetime
import json
from urllib.parse import parse_qs

from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import escape_uri_path


class AnalyticsPolicy:
    """
    Determines whether Google Analytics is enabled.
    Apps can require analytics or allow users to choose (by setting a long-lived cookie).
    """
    cookie_name = 'cookie_policy'

    def __init__(self, request):
        self.google_analytics_id = getattr(settings, 'GOOGLE_ANALYTICS_ID', None)
        analytics_required = getattr(settings, 'ANALYTICS_REQUIRED', True)
        self.enabled = self.google_analytics_id and (analytics_required or self.is_cookie_policy_accepted(request))

    def is_cookie_policy_accepted(self, request):
        """
        Checks for cookie policy being accepted in a cookie.
        Lack of cookie policy indicates that analytics should NOT enabled.
        """
        cookie_policy = request.COOKIES.get(self.cookie_name, '')
        try:
            cookie_policy = json.loads(cookie_policy)
            return isinstance(cookie_policy, dict) and cookie_policy.get('usage') is True
        except ValueError:
            return False

    def set_cookie_policy(self, response, accepted: bool):
        """
        Set cookie policy using long-lived cookie.
        """
        expires = timezone.now() + datetime.timedelta(days=365)
        cookie_policy = {'usage': accepted}
        response.set_cookie(self.cookie_name, json.dumps(cookie_policy), expires=expires, secure=True, httponly=True)


def _get_qs_value(qs, key):
    value = qs.get(key, [])
    if not value:
        return None
    return escape_uri_path(value[0])


def genericised_pageview(request, title=None):
    urlparts = request.build_absolute_uri().split('?', 1)

    location = urlparts.pop(0)
    if location.startswith('//'):
        location = f'https:{location}'

    if urlparts:
        qs = parse_qs(urlparts.pop(0))
    else:
        qs = {}

    return {
        'page': escape_uri_path(request.path),
        'location': escape_uri_path(location),
        'title': title,
        'campaignName': _get_qs_value(qs, 'utm_campaign'),
        'campaignMedium': _get_qs_value(qs, 'utm_medium'),
        'campaignSource': _get_qs_value(qs, 'utm_source'),
    }


class ReferrerPolicyMiddleware(MiddlewareMixin):
    def process_response(self, _, response):
        response['Referrer-Policy'] = 'same-origin'
        return response
