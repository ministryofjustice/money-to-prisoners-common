from collections import OrderedDict
import re

from django import template
from django.conf import settings
from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils.translation import override
try:
    from raven.contrib.django.models import client as sentry_client
except ImportError:
    sentry_client = None

register = template.Library()


@register.filter
def to_string(value):
    return str(value)


class StripWhitespaceNode(template.Node):
    def __init__(self, node_list):
        self.node_list = node_list

    def render(self, context):
        output = self.node_list.render(context)
        return re.sub(r'\s+', '', output)


@register.tag
def stripwhitespace(parser, token):
    if len(token.split_contents()) != 1:
        raise template.TemplateSyntaxError('stripwhitespace takes no arguments')
    node_list = parser.parse(('endstripwhitespace',))
    parser.delete_first_token()
    return StripWhitespaceNode(node_list)


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


@register.inclusion_tag('mtp_common/language-switch.html', takes_context=True)
def language_switch(context):
    request = context.get('request')
    urls = []
    try:
        if not settings.SHOW_LANGUAGE_SWITCH:
            raise NoReverseMatch
        view_name = request.resolver_match.view_name
        url_args = request.resolver_match.args
        url_kwargs = request.resolver_match.kwargs
        for lang_code, lang_name in settings.LANGUAGES:
            with override(lang_code):
                urls.append((lang_code, lang_name, reverse(view_name, args=url_args, kwargs=url_kwargs)))
    except (AttributeError, NoReverseMatch):
        urls = []
    return {'urls': urls}
