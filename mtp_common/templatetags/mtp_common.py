from collections import OrderedDict

from django import template
try:
    from raven.contrib.django.models import client as sentry_client
except ImportError:
    sentry_client = None

register = template.Library()


@register.filter
def to_string(value):
    return str(value)


@register.filter
def field_from_name(form, name):
    if name in form.fields:
        return form[name]


@register.simple_tag
def get_form_errors(form):
    """
    Django form errors do not obey natural field order,
    this template tag returns non-field and field-specific errors
    :param form: the form instance
    """
    return {
        'non_field': form.non_field_errors(),
        'field_specific': OrderedDict(
            (field, form.errors[field.name])
            for field in form
            if field.name in form.errors
        )
    }


@register.inclusion_tag('mtp_common/sentry-js.html')
def sentry_js():
    sentry_dsn = None
    if sentry_client is not None:
        sentry_dsn = sentry_client.get_public_dsn('https') or None
    return {
        'sentry_dsn': sentry_dsn
    }
