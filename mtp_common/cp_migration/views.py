from django.conf import settings
from django.shortcuts import render
from django.utils.cache import add_never_cache_headers


def get_maintenance_response(request):
    """
    Returns a 503 response with no-cache header and retry-after header.
    """
    response = render(
        request,
        'mtp_common/cp_migration/maintenance.html',
        status=503,
    )
    response['Retry-After'] = 5 * 60 * 60  # 5 hours
    add_never_cache_headers(response)
    return response


def get_we_have_moved_response(request):
    """
    Returns a 200 response with details of the new url.
    """
    new_domain = getattr(settings, 'CLOUD_PLATFORM_MIGRATION_URL', '')
    response = render(
        request,
        'mtp_common/cp_migration/we-have-moved.html',
        context={
            'new_url': f'{new_domain}{request.get_full_path()}',
        },
    )
    return response
