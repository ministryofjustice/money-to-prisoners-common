import decimal
import re

from django.utils.translation import gettext


def and_join(values):
    if not isinstance(values, list):
        values = list(values)
    if len(values) > 1:
        values = values[:-2] + [gettext('%s and %s') % (values[-2], values[-1])]
    return ', '.join(map(str, values))


def format_currency(pence, symbol='£', trim_empty_pence=False):
    if not isinstance(pence, (int, decimal.Decimal)) or isinstance(pence, bool):
        return
    if pence < 0:
        neg = '-'
        pence = abs(pence)
    else:
        neg = ''
    text = f'{neg}{symbol}{pence / 100:,.2f}'
    if trim_empty_pence and text.endswith('.00'):
        text = text[:-3]
    return text


def format_postcode(value):
    matches = re.match(r'^([A-Z]{1,2}\d{1,2}[A-Z]?)\s*(\d[A-Z]{2})$', value, flags=re.IGNORECASE)
    if matches:
        return f'{matches.group(1).upper()} {matches.group(2).upper()}'
    return value.upper()
