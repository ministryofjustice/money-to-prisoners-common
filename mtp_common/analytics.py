from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import escape_uri_path


def genericised_pageview(request, title=None):
    location = request.build_absolute_uri().split('?')[0]
    if location.startswith('//'):
        location = 'https:%s' % location
    pageview = {
        'page': escape_uri_path(request.path),
        'location': escape_uri_path(location),
    }
    if title:
        pageview['title'] = title
    return pageview


def default_genericised_pageview(request):
    return {
        'default_google_analytics_pageview': genericised_pageview(request)
    }


class ReferrerPolicyMiddleware(MiddlewareMixin):
    def process_response(self, _, response):
        response['Referrer-Policy'] = 'same-origin'
        return response
