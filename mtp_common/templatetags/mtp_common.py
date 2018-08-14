from collections import OrderedDict
from itertools import chain
import json
import re

from django import template
from django.conf import settings
from django.forms.utils import flatatt
from django.template.base import token_kwargs
from django.urls import NoReverseMatch, reverse
from django.utils.crypto import get_random_string
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.translation import gettext, override

from mtp_common.api import notifications_for_request

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


@register.filter
def wrapwithtag(content, tag):
    return format_html('<{tag}>{content}</{tag}>', tag=tag, content=content)


@register.filter
def wraplink(text, url):
    return format_html('<a href="{url}">{text}</a>', text=text, url=url)


@register.simple_tag
def labelled_data(label, value, tag='div', url=None):
    element_id = get_random_string(length=4)
    if url:
        value = format_html('<a href="{url}">{value}</a>', value=value, url=url)
    return format_html(
        '''
        <div id="mtp-label-{element_id}" class="mtp-detail-label">{label}</div>
        <{tag} aria-labelledby="mtp-label-{element_id}">{value}</{tag}>
        ''',
        element_id=element_id, label=label, value=value, tag=tag
    )


@register.filter
def hide_long_text(text, count=5):
    if not text:
        return text
    count = int(count)
    words = text.split()
    if len(words) <= count:
        return text
    short_text, rest_text = ' '.join(words[:count]), ' '.join(words[count:])
    return format_html('<span class="visually-hidden">{text}</span>'
                       '<span aria-hidden="true">'
                       '  {short_text}'
                       '  <a href="#" class="js-long-text" data-rest="{rest_text}">{more}</a>'
                       '</span>',
                       short_text=short_text, rest_text=rest_text, text=text, more=gettext('More…'))


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


def make_alternate_language_urls(request):
    alt_urls = []
    try:
        if not settings.SHOW_LANGUAGE_SWITCH:
            raise NoReverseMatch
        view_name = request.resolver_match.view_name
        url_args = request.resolver_match.args
        url_kwargs = request.resolver_match.kwargs
        for lang_code, lang_name in settings.LANGUAGES:
            with override(lang_code):
                alt_urls.append((lang_code, lang_name, reverse(view_name, args=url_args, kwargs=url_kwargs)))
    except (AttributeError, NoReverseMatch):
        alt_urls = []
    return alt_urls


@register.inclusion_tag('mtp_common/includes/language-switch.html', takes_context=True)
def language_switch(context):
    request = context.get('request')
    return {
        'alt_urls': make_alternate_language_urls(request),
    }


@register.inclusion_tag('mtp_common/sub-nav.html', takes_context=True)
def sub_nav(context):
    """
    Sub-nav displayed below proposition header
    - creates alternate language links if SHOW_LANGUAGE_SWITCH is set
    - takes "breadcrumbs" from the context
    - takes "breadcrumbs_back" from the context to show a back link *instead* of breadcrumbs
    """
    request = context.get('request')
    return {
        'alt_urls': make_alternate_language_urls(request),
        'breadcrumbs': context.get('breadcrumbs'),
        'breadcrumbs_back': context.get('breadcrumbs_back'),
    }


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


class DialogueNode(template.Node):
    template_name = 'mtp_common/includes/dialogue-box.html'

    def __init__(self, node_list, title=None, urgent=None, show_close_button=None, html_id=None, html_classes=None):
        self.node_list = node_list
        self.title = title
        self.urgent = urgent
        self.show_close_button = show_close_button
        self.html_id = html_id or 'mtp-dialogue-%s' % get_random_string(length=4)
        self.html_classes = html_classes

    def render(self, context):
        context.push()

        context['dialogue_id'] = self.html_id.resolve(context) if hasattr(self.html_id, 'resolve') else self.html_id
        if self.html_classes:
            context['dialogue_classes'] = self.html_classes.resolve(context)
        urgent = self.urgent and self.urgent.resolve(context)
        context['dialogue_role'] = 'alertdialog' if urgent else 'dialog'
        if self.title:
            context['dialogue_title'] = self.title.resolve(context)
        if self.show_close_button:
            context['dialogue_close_button'] = self.show_close_button.resolve(context)
        context['dialogue_close_class'] = 'js-dialogue-close'

        context['dialogue_contents'] = self.node_list.render(context)

        dialogue_template = context.template.engine.get_template(self.template_name)
        rendered_html = dialogue_template.render(context)

        context.pop()
        return rendered_html


@register.tag
def dialoguebox(parser, token):
    kwargs = token_kwargs(token.split_contents()[1:], parser)
    node_list = parser.parse(('enddialoguebox',))
    parser.delete_first_token()
    return DialogueNode(node_list, **kwargs)


@register.inclusion_tag('mtp_common/includes/notifications.html')
def notifications_box(request, *targets, **kwargs):
    for target in targets:
        notifications = notifications_for_request(request, target, **kwargs)
        if notifications:
            return {
                'notifications': notifications
            }


class TabbedPanelNode(template.Node):
    template_name = 'mtp_common/includes/tabbed-panel.html'

    def __init__(self, node_list, cookie_name=None, tab_label=None):
        self.node_list = node_list
        self.cookie_name = cookie_name
        self.tab_label = tab_label

    def render(self, context):
        tabs = []
        tab_nodes = template.NodeList()
        other_nodes = template.NodeList()
        for node in self.node_list:
            if isinstance(node, PanelTabNode):
                tab_nodes.append(node)
                name = node.name.resolve(context)
                panel_id = 'mtp-tabpanel-%s' % name
                tabs.append({
                    'title': node.title.resolve(context),
                    'attrs': flatatt({
                        'id': 'mtp-tab-%s' % name,
                        'href': '#%s' % panel_id,
                        'role': 'tab',
                        'aria-controls': panel_id,
                        'aria-flowto': panel_id,
                    }),
                })
            else:
                other_nodes.append(node)

        tab_content = tab_nodes.render(context)
        other_content = other_nodes.render(context)
        cookie_name = self.cookie_name.resolve(context) if self.cookie_name else ''
        tab_label = self.tab_label.resolve(context) if self.tab_label else ''
        context.push()
        context['cookie_name'] = cookie_name
        context['tab_label'] = tab_label
        context['tabs'] = tabs
        context['tab_content'] = tab_content
        context['other_content'] = other_content
        tabbed_content = context.template.engine.get_template(self.template_name)
        rendered_html = tabbed_content.render(context)
        context.pop()
        return rendered_html


@register.tag
def tabbedpanel(parser, token):
    kwargs = token_kwargs(token.split_contents()[1:], parser)
    node_list = parser.parse(('endtabbedpanel',))
    parser.delete_first_token()
    return TabbedPanelNode(node_list, **kwargs)


class PanelTabNode(template.Node):
    template_name = 'mtp_common/includes/panel-tab.html'

    def __init__(self, node_list, name=None, title=None):
        self.node_list = node_list
        if not name or not title:
            raise template.TemplateSyntaxError('name and title must be provided')
        self.name = name
        self.title = title

    def render(self, context):
        name = self.name.resolve(context)
        content = self.node_list.render(context)
        context.push()
        context['name'] = name
        context['content'] = content
        tab_template = context.template.engine.get_template(self.template_name)
        rendered_html = tab_template.render(context)
        context.pop()
        return rendered_html


@register.tag
def paneltab(parser, token):
    kwargs = token_kwargs(token.split_contents()[1:], parser)
    node_list = parser.parse(('endpaneltab',))
    parser.delete_first_token()
    return PanelTabNode(node_list, **kwargs)


@register.inclusion_tag('mtp_common/includes/sortable-cell.html')
def sortable_cell(title, params, field, url_prefix='', cell_classes='', ignored_fields=('page',)):
    current_ordering = params.get('ordering')
    reversed_params = {
        key: value
        for key, value in params.items()
        if value and key not in ignored_fields
    }
    reversed_params['ordering'] = field

    link_classes = ['mtp-sortable-cell']
    if current_ordering == field:
        screenreader_description = gettext('In ascending order')
        link_classes.append('mtp-sortable-cell--asc')
        reversed_params['ordering'] = '-%s' % field
    elif current_ordering == '-%s' % field:
        screenreader_description = gettext('In descending order')
        link_classes.append('mtp-sortable-cell--desc')
    else:
        screenreader_description = ''

    query_string = urlencode(reversed_params, doseq=True)
    return {
        'title': title,
        'url_prefix': url_prefix,
        'query_string': query_string,
        'screenreader_description': screenreader_description,
        'link_classes': ' '.join(link_classes),
        'cell_classes': cell_classes,
    }
