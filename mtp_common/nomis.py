from datetime import date
import time

from django.conf import settings
import jwt
from mtp_common.auth import urljoin
import requests


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


def get(path, params=None, timeout=15, retries=0):
    if params:
        params = {
            param: params[param] for param in params
            if params[param] is not None
        }
    response = requests.get(
        build_nomis_url(path),
        params=params,
        headers=generate_request_headers(),
        timeout=timeout
    )
    if response.status_code >= 500 and retries > 0:
        return get(path, params, timeout, retries-1)

    response.raise_for_status()
    if response.status_code != requests.codes.no_content:
        return response.json()
    return {'status_code': response.status_code}


def post(path, data=None, timeout=15, retries=0):
    response = requests.post(
        build_nomis_url(path),
        json=data,
        headers=generate_request_headers(),
        timeout=timeout
    )
    if response.status_code >= 500 and retries > 0:
        return post(path, data, timeout, retries-1)

    response.raise_for_status()
    if response.status_code != requests.codes.no_content:
        return response.json()
    return {'status_code': response.status_code}


def get_account_balances(prison_id, prisoner_number, retries=0):
    return get(
        '/prison/{prison_id}/offenders/{prisoner_number}/accounts'.format(
            prison_id=prison_id, prisoner_number=prisoner_number
        ),
        retries=retries
    )


def get_transaction_history(prison_id, prisoner_number, account_code,
                            from_date, to_date=None, retries=0):
    params = {
        'from_date': convert_date_param(from_date),
        'to_date': convert_date_param(to_date),
    }
    return get(
        '/prison/{prison_id}/offenders/{prisoner_number}/accounts/{account_code}/transactions'.format(
            prison_id=prison_id, prisoner_number=prisoner_number, account_code=account_code
        ),
        params=params,
        retries=retries
    )


def credit_prisoner(prison_id, prisoner_number, amount, credit_id, description, retries=0):
    data = {
        'type': 'MRPR',
        'description': description,
        'amount': amount,
        'client_transaction_id': str(credit_id),
        'client_unique_ref': str(credit_id)
    }
    return post(
        '/prison/{prison_id}/offenders/{prisoner_number}/transactions'.format(
            prison_id=prison_id, prisoner_number=prisoner_number
        ),
        data,
        retries=retries
    )


def get_photograph_data(prisoner_number, retries=0):
    result = get(
        '/offenders/{prisoner_number}/image'.format(prisoner_number=prisoner_number),
        retries=retries
    )
    if result.get('image'):
        return result['image']


def get_location(prisoner_number, retries=0):
    result = get(
        '/offenders/{prisoner_number}/location'.format(prisoner_number=prisoner_number),
        retries=retries
    )
    if 'establishment' in result:
        return {
            'nomis_id': result['establishment']['code'],
            'name': result['establishment']['desc'],
        }
