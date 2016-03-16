from django import template
try:
    from raven.contrib.django.models import client as sentry_client
except ImportError:
    sentry_client = None

register = template.Library()


@register.filter()
def to_string(value):
    return str(value)


@register.filter(is_safe=True)
def safewrap(val, arg):
    return val.format(arg)


@register.filter()
def field_from_name(form, name):
    if name in form.fields:
        return form[name]


@register.inclusion_tag('mtp_utils/sentry-js.html')
def sentry_js():
    sentry_dsn = None
    if sentry_client is not None:
        sentry_dsn = sentry_client.get_public_dsn('https') or None
    return {
        'sentry_dsn': sentry_dsn
    }
