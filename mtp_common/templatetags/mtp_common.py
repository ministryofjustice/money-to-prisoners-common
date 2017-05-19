from collections import OrderedDict
from itertools import chain
import json
import re

from django import template
from django.conf import settings
from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils.crypto import get_random_string
from django.utils.translation import override
try:
    from raven.contrib.django.models import client as sentry_client
except ImportError:
    sentry_client = None

register = template.Library()


@register.filter
def separate_thousands(value):
    if not isinstance(value, int):
        return value
    return '{:,}'.format(value)


@register.filter
def to_string(value):
    return str(value)


@register.simple_tag
def random_string(length=4):
    return get_random_string(length=length)


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


@register.inclusion_tag('mtp_common/includes/page-list.html')
def page_list(page, page_count, query_string=None, end_padding=1, page_padding=2):
    if page_count < 7:
        pages_with_ellipses = range(1, page_count + 1)
    else:
        pages = sorted(set(chain(
            range(1, end_padding + 2),
            range(page - page_padding, page + page_padding + 1),
            range(page_count - end_padding, page_count + 1),
        )))
        pages_with_ellipses = []
        last_page = 0
        for index in pages:
            if index < 1 or index > page_count:
                continue
            if last_page + 1 < index:
                pages_with_ellipses.append(None)
            pages_with_ellipses.append(index)
            last_page = index
    return {
        'page': page,
        'page_count': page_count,
        'page_range': pages_with_ellipses,
        'query_string': query_string,
    }


@register.inclusion_tag('mtp_common/includes/footer-feedback.html')
def footer_feedback_form(request, context):
    return_errors_param = context.get('return_errors_param', 'feedback_errors')
    try:
        errors = json.loads(request.GET[return_errors_param])
    except (KeyError, TypeError, ValueError):
        errors = None
    return dict(
        context,
        request=request,
        return_errors_param=return_errors_param,
        errors=errors,
    )
