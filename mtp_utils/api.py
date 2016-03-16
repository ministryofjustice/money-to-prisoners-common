from django.conf import settings


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
