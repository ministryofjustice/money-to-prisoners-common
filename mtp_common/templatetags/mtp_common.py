from collections import OrderedDict
from itertools import chain
import re

from django import template
from django.conf import settings
from django.contrib import messages
from django.forms.utils import flatatt
from django.template.base import token_kwargs
from django.urls import NoReverseMatch, reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.translation import gettext, gettext_lazy as _, override

from mtp_common.api import notifications_for_request
from mtp_common.utils import and_join, format_postcode

try:
    from sentry_sdk import client as sentry_client
except ImportError:
    sentry_client = None

register = template.Library()


@register.filter(name='and_join')
def and_join_filter(values):
    return and_join(values)


@register.filter
def separate_thousands(value):
    if not isinstance(value, int):
        return value
    return '{:,}'.format(value)


@register.filter
def postcode(value):
    if not value or not isinstance(value, str):
        return value
    return format_postcode(value)


@register.filter
def to_string(value):
    # TODO: use force_text?
    return str(value)


@register.simple_tag(takes_context=True)
def create_counter(context, var):
    context[var] = 0
    return ''


@register.simple_tag(takes_context=True)
def increment_counter(context, var):
    context[var] += 1
    return context[var]


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
def labelled_data(label, value, tag='div', url=None, element_id=None):
    element_id = element_id or f'mtp-labelled-data-{get_random_string(length=4)}'
    if url:
        value = format_html('<a href="{url}">{value}</a>', value=value, url=url)
    return format_html(
        """
        <div class="mtp-labelled-data">
        <div id="{element_id}" class="mtp-labelled-data__label">{label}</div>
        <{tag} class="mtp-labelled-data__data" aria-labelledby="{element_id}">{value}</{tag}>
        </div>
        """,
        element_id=element_id,
        label=label,
        value=value,
        tag=tag,
    )


@register.filter
def hide_long_text(text, count=5):
    if not text:
        return text
    count = int(count)
    words = force_text(text).split()
    if len(words) <= count:
        return text
    short_text, rest_text = ' '.join(words[:count]), ' '.join(words[count:])
    return format_html(
        '<span class="govuk-visually-hidden">{text}</span>'
        '<span aria-hidden="true">'
        '  {short_text}'
        '  <a href="#" class="mtp-hidden-long-text" data-rest="{rest_text}">{more}</a>'
        '</span>',
        short_text=short_text,
        rest_text=rest_text,
        text=text,
        more=gettext('More…'),
    )


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


class CaptureOutputNode(template.Node):
    def __init__(self, node_list, variable):
        self.node_list = node_list
        self.variable = variable

    def render(self, context):
        context[self.variable] = self.node_list.render(context)
        return ''


@register.tag
def captureoutput(parser, token):
    """
    Use this tag to capture template output into a variable;
    useful for including complex content into a blocktrans
    """
    args = token.split_contents()[1:]
    if len(args) != 2 or args[0] != 'as':
        raise template.TemplateSyntaxError('captureoutput requires "as variable"')
    node_list = parser.parse(('endcaptureoutput',))
    parser.delete_first_token()
    return CaptureOutputNode(node_list, args[1])


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
    if sentry_client:
        return {
            'environment': settings.ENVIRONMENT,
            'app_git_commit': settings.APP_GIT_COMMIT,
            'sentry_dsn': sentry_client.get_options().get('dsn')
        }
    else:
        return {
            'sentry_dsn': ''
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


@register.inclusion_tag('mtp_common/components/language-switch.html', takes_context=True)
def language_switch(context):
    request = context.get('request')
    return {
        'alt_urls': make_alternate_language_urls(request),
    }


@register.inclusion_tag('mtp_common/components/breadcrumb-bar.html', takes_context=True)
def breadcrumb_bar(context):
    """
    Breadcrumbs and language switcher displayed below proposition header
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


@register.inclusion_tag('mtp_common/components/card-group.html')
def card_group(cards, columns=3):
    if columns not in (2, 3, 4):
        raise template.TemplateSyntaxError('columns must be 2, 3 or 4')
    return {
        'cards': cards,
        'columns': columns,
    }


@register.inclusion_tag('mtp_common/components/page-list.html')
def page_list(page, page_count, query_string=None, end_padding=0, page_padding=1):
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
        'query_string': f'{query_string}&' if query_string else '',
    }


class DialogueNode(template.Node):
    template_name = 'mtp_common/components/dialogue-box.html'

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


@register.inclusion_tag('mtp_common/components/notification-banners.html')
def notification_banners(request, *targets, **kwargs):
    """
    Shows notification banners from:
    - mtp-api's _first_ target that responds
    - django messages
    """
    context_data = {
        'notifications': [],
        'messages': messages.get_messages(request),
    }
    for target in targets:
        notifications = notifications_for_request(request, target, **kwargs)
        if notifications:
            context_data['notifications'] = notifications
            break
    return context_data


NOTIFICATION_LEVELS = {
    'info': _('Information'),
    'success': _('Success'),
    'warning': _('Warning'),
    'error': _('Error'),
}


@register.filter
def notification_level(level_name):
    return NOTIFICATION_LEVELS.get(level_name, _('Important'))


class AccordionNode(template.Node):
    template_name = 'mtp_common/components/accordion.html'

    def __init__(self, node_list, name):
        self.node_list = node_list
        self.name = name

    def render(self, context):
        name = self.name.resolve(context)
        accordion_content = ''
        other_nodes = template.NodeList()
        counter = 0
        for node in self.node_list:
            if isinstance(node, AccordionSectionNode):
                counter += 1
                context.push()
                context['name'] = name
                context['section_counter'] = counter
                accordion_content += node.render(context)
                context.pop()
            else:
                other_nodes.append(node)
        other_content = other_nodes.render(context)
        context.push()
        context['accordion_content'] = accordion_content
        context['other_content'] = other_content
        accordion_template = context.template.engine.get_template(self.template_name)
        rendered_html = accordion_template.render(context)
        context.pop()
        return rendered_html


@register.tag
def accordion(parser, token):
    kwargs = token_kwargs(token.split_contents()[1:], parser)
    if not kwargs.get('name'):
        raise template.TemplateSyntaxError('accordion requires name argument')
    node_list = parser.parse(('endaccordion',))
    parser.delete_first_token()
    return AccordionNode(node_list, **kwargs)


class AccordionSectionNode(template.Node):
    template_name = 'mtp_common/components/accordion-section.html'

    def __init__(self, node_list, heading):
        self.node_list = node_list
        self.heading = heading

    def render(self, context):
        heading = self.heading.resolve(context)
        content = self.node_list.render(context)
        context.push()
        context['heading'] = heading
        context['content'] = content
        tab_template = context.template.engine.get_template(self.template_name)
        rendered_html = tab_template.render(context)
        context.pop()
        return rendered_html


@register.tag
def accordionsection(parser, token):
    kwargs = token_kwargs(token.split_contents()[1:], parser)
    if 'heading' not in kwargs:
        raise template.TemplateSyntaxError('accordion section requires heading argument')
    node_list = parser.parse(('endaccordionsection',))
    parser.delete_first_token()
    return AccordionSectionNode(node_list, **kwargs)


class TabbedPanelNode(template.Node):
    template_name = 'mtp_common/components/tabbed-panel.html'

    def __init__(
        self,
        node_list,
        cookie_name=None,
        tab_label=None,
        collapsable=None,
        css_class=None,
    ):
        """
        Params:
        - cookie_name: name of the cookie in which to hold the state (selected tab, collapsed or expanded etc.)
        - tab_label: to be used as aria-label
        - collapsable (default True): if the selected tab should collapse when re-selected
        - css_class: (optional) extra css class to append to the container.
        """
        self.node_list = node_list
        self.cookie_name = cookie_name
        self.tab_label = tab_label
        self.collapsable = collapsable
        self.css_class = css_class

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
        collapsable = self.collapsable.resolve(context) if self.collapsable else True
        css_class = self.css_class.resolve(context) if self.css_class else ''
        context.push()
        context['cookie_name'] = cookie_name
        context['css_class'] = css_class
        context['collapsable'] = collapsable
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
    template_name = 'mtp_common/components/panel-tab.html'

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


@register.inclusion_tag('mtp_common/components/sortable-cell.html')
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
