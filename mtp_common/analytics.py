from django.utils.encoding import escape_uri_path


def genericised_pageview(request, title):
    location = request.build_absolute_uri().split('?')[0]
    if location.startswith('//'):
        location = 'https:%s' % location
    return {
        'page': escape_uri_path(request.path),
        'location': escape_uri_path(location),
        'title': title,
    }
