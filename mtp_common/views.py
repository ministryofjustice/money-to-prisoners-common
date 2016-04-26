from django.views import defaults


def page_not_found(request, exception, template_name='mtp_common/errors/404.html'):
    return defaults.page_not_found(request, exception, template_name)


def server_error(request, template_name='mtp_common/errors/500.html'):
    return defaults.server_error(request, template_name)


def bad_request(request, exception, template_name='mtp_common/errors/400.html'):
    return defaults.bad_request(request, exception, template_name)
