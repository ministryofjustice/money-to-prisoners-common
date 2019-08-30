from urllib.parse import parse_qs

from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import escape_uri_path


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


def default_genericised_pageview(request):
    return {
        'default_google_analytics_pageview': genericised_pageview(request)
    }


class ReferrerPolicyMiddleware(MiddlewareMixin):
    def process_response(self, _, response):
        response['Referrer-Policy'] = 'same-origin'
        return response
