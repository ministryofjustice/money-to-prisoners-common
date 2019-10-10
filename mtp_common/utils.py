import json
import re

from django.utils.translation import gettext


def and_join(values):
    if not isinstance(values, list):
        values = list(values)
    if len(values) > 1:
        values = values[:-2] + [gettext('%s and %s') % (values[-2], values[-1])]
    return ', '.join(map(str, values))


def format_postcode(value):
    matches = re.match(r'^([A-Z]{1,2}\d{1,2}[A-Z]?)\s*(\d[A-Z]{2})$', value, flags=re.IGNORECASE)
    if matches:
        return f'{matches.group(1).upper()} {matches.group(2).upper()}'
    return value.upper()


class CookiePolicy:
    """
    A configurable cookie policy loaded from a cookie.
    Attributes on the policy object represent different settings.
    "usage", which is on by default, represents whether Google Analytics should be enabled.
    Additional keys can be added when the object is instantiated,
    but otherwise all other cookie contents are ignored.
    """
    cookie_name = 'cookie_policy'

    def __init__(self, request, **defaults):
        defaults.setdefault('usage', True)
        cookie_policy = request.COOKIES.get(self.cookie_name, '')
        try:
            cookie_policy = json.loads(cookie_policy)
            if not isinstance(cookie_policy, dict):
                raise ValueError
            cookie_policy = {
                policy_key: bool(cookie_policy.get(policy_key, default_value))
                for policy_key, default_value in defaults.items()
            }
        except ValueError:
            cookie_policy = defaults.copy()
        self.__dict__ = cookie_policy
