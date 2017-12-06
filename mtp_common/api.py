import json
import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from requests.exceptions import RequestException

from mtp_common.auth import api_client

logger = logging.getLogger('mtp')


def api_errors_to_messages(request, error, fallback_text):
    """
    Adds messages for each error returned from the MTP apis
    Useful for displaying errors when there's no form on the page
    :param request: HttpRequest
    :param error: HttpClientError
    :param fallback_text: fallback error text
    """
    try:
        response_body = json.loads(error.content.decode('utf-8'))
        for field, errors in response_body.items():
            if isinstance(errors, list):
                for error in errors:
                    messages.error(request, error)
            else:
                messages.error(request, errors)
    except (AttributeError, ValueError, KeyError):
        messages.error(request, fallback_text)


def retrieve_all_pages(api_endpoint, **kwargs):
    """
    Some MTP apis are paginated using Django Rest Framework's LimitOffsetPagination paginator,
    this method loads all pages into a single results list
    :param api_endpoint: slumber callable, e.g. `[api_client].cashbook.transactions.locked.get`
    :param kwargs: additional arguments to pass into api callable
    """
    page_size = getattr(settings, 'REQUEST_PAGE_SIZE', 20)
    loaded_results = []

    offset = 0
    while True:
        response = api_endpoint(limit=page_size, offset=offset,
                                **kwargs)
        count = response.get('count', 0)
        loaded_results += response.get('results', [])
        if len(loaded_results) >= count:
            break
        offset += page_size

    return loaded_results


def retrieve_all_pages_for_path(session, path, **params):
    """
    Some MTP apis are paginated using Django Rest Framework's LimitOffsetPagination paginator,
    this method loads all pages into a single results list
    :param session: Requests Session object
    :param path: URL path
    :param params: additional URL params
    """
    page_size = getattr(settings, 'REQUEST_PAGE_SIZE', 20)
    loaded_results = []

    offset = 0
    while True:
        response = session.get(
            path,
            params=dict(limit=page_size, offset=offset, **params)
        )
        content = response.json()
        count = content.get('count', 0)
        loaded_results += content.get('results', [])
        if len(loaded_results) >= count:
            break
        offset += page_size

    return loaded_results


def notifications_for_request(request, target=None, use_cache=True):
    # NB: caching can only be used since notifications are not currently set up to be user/request specific
    cache_key = 'notifications-%s' % target
    if use_cache:
        results = cache.get(cache_key)
        if results:
            return results
    try:
        if request.user.is_authenticated:
            session = api_client.get_api_session(request)
        else:
            session = api_client.get_unauthenticated_session()
        response = session.get('notifications/', params={'target__startswith': target} if target else None)
        results = response.json()['results']
        if use_cache:
            cache.set(cache_key, results, timeout=60 * 5)
        return results
    except (RequestException, ValueError, KeyError):
        logger.exception('Could not load notifications')
