from datetime import date
import time
from urllib.parse import quote_plus

from django.conf import settings
import jwt
from mtp_common.auth import urljoin
import requests
from requests.exceptions import ConnectionError


def convert_date_param(param):
    if isinstance(param, date):
        return param.isoformat()
    elif isinstance(param, str):
        return param
    return None


def generate_request_headers():
    encoded = jwt.encode(
        {'iat': int(time.time()), 'token': settings.NOMIS_API_CLIENT_TOKEN},
        settings.NOMIS_API_PRIVATE_KEY, 'ES256'
    )
    bearer_token = encoded.decode('utf8')
    return {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % bearer_token
    }


def build_nomis_url(path):
    return urljoin(settings.NOMIS_API_BASE_URL, path)


def get(path, params=None, timeout=15, retries=0, session=None):
    if params:
        params = {
            param: params[param] for param in params
            if params[param] is not None
        }
    session_or_module = session or requests
    try:
        response = session_or_module.get(
            build_nomis_url(path),
            params=params,
            headers=generate_request_headers(),
            timeout=timeout
        )
    except ConnectionError as e:
        if retries > 0:
            return get(path, params, timeout, retries-1, session=session)
        raise e
    if response.status_code >= 500 and retries > 0:
        return get(path, params, timeout, retries-1, session=session)

    response.raise_for_status()
    if response.status_code != requests.codes.no_content:
        return response.json()
    return {'status_code': response.status_code}


def post(path, data=None, timeout=15, retries=0, session=None):
    session_or_module = session or requests
    try:
        response = session_or_module.post(
            build_nomis_url(path),
            json=data,
            headers=generate_request_headers(),
            timeout=timeout
        )
    except ConnectionError as e:
        if retries > 0:
            return post(path, data, timeout, retries-1, session=session)
        raise e
    if response.status_code >= 500 and retries > 0:
        return post(path, data, timeout, retries-1, session=session)

    response.raise_for_status()
    if response.status_code != requests.codes.no_content:
        return response.json()
    return {'status_code': response.status_code}


def get_account_balances(prison_id, prisoner_number, retries=0, session=None):
    return get(
        '/prison/{prison_id}/offenders/{prisoner_number}/accounts'.format(
            prison_id=quote_plus(prison_id),
            prisoner_number=quote_plus(prisoner_number)
        ),
        retries=retries, session=session
    )


def get_transaction_history(prison_id, prisoner_number, account_code,
                            from_date, to_date=None, retries=0, session=None):
    params = {
        'from_date': convert_date_param(from_date),
        'to_date': convert_date_param(to_date),
    }
    return get(
        '/prison/{prison_id}/offenders/{prisoner_number}/accounts/{account_code}/transactions'.format(
            prison_id=quote_plus(prison_id),
            prisoner_number=quote_plus(prisoner_number),
            account_code=quote_plus(account_code)
        ),
        params=params, retries=retries, session=session
    )


def create_transaction(prison_id, prisoner_number, amount, record_id,
                       description, transaction_type, retries=0, session=None):
    data = {
        'type': transaction_type,
        'description': description,
        'amount': amount,
        'client_transaction_id': str(record_id),
        'client_unique_ref': str(record_id)
    }
    return post(
        '/prison/{prison_id}/offenders/{prisoner_number}/transactions'.format(
            prison_id=quote_plus(prison_id),
            prisoner_number=quote_plus(prisoner_number)
        ),
        data, retries=retries, session=session
    )


def get_photograph_data(prisoner_number, retries=0, session=None):
    result = get(
        '/offenders/{prisoner_number}/image'.format(
            prisoner_number=quote_plus(prisoner_number)
        ),
        retries=retries, session=session
    )
    if result.get('image'):
        return result['image']


def get_location(prisoner_number, retries=0, session=None):
    result = get(
        '/offenders/{prisoner_number}/location'.format(
            prisoner_number=quote_plus(prisoner_number)
        ),
        retries=retries, session=session
    )
    if 'establishment' in result:
        location = {
            'nomis_id': result['establishment']['code'],
            'name': result['establishment']['desc'],
        }
        if 'housing_location' in result:
            housing = result['housing_location']
            if isinstance(housing, str):
                housing = {'description': housing}
                levels = housing['description'].split('-')
                levels.pop(0)  # disregard prison code
                levels = [
                    {'type': k, 'value': v}
                    for k, v in zip(('Wing', 'Landing', 'Cell'), levels)
                ]
                housing['levels'] = levels
            location['housing_location'] = housing
        return location
