from urllib.parse import urlparse, urlunparse

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.forms.utils import ErrorDict, ErrorList
from django.http import HttpResponse, QueryDict
from django.shortcuts import redirect
from django.utils.http import is_safe_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from requests.exceptions import HTTPError
from zendesk_tickets.forms import EmailTicketForm


class FeedbackFooterView(FormView):
    form_class = EmailTicketForm
    subject = 'MTP Feedback'
    tags = ('mtp', 'feedback')
    ticket_template_name = 'zendesk_tickets/ticket.txt'
    return_errors_param = 'feedback_errors'

    def get_success_url(self, referer=None):
        return_to = referer or self.request.META.get('HTTP_REFERER')
        if not is_safe_url(url=return_to, host=self.request.get_host()):
            return_to = '/'
        return return_to

    def make_response(self, referer=None, errors=None):
        if errors:
            errors = errors.as_json()
        if self.request.is_ajax():
            return HttpResponse('{"%s":%s}' % (self.return_errors_param, errors or 'null'),
                                content_type='application/json')

        return_to = self.get_success_url(referer=referer)
        return_to = list(urlparse(return_to))
        query = QueryDict(query_string=return_to[4], mutable=True)
        if errors:
            query[self.return_errors_param] = errors
        else:
            query.pop(self.return_errors_param, None)
        return_to[4] = query.urlencode()
        return_to = urlunparse(return_to)
        return redirect(return_to)

    def get(self, request, *args, **kwargs):
        errors = ErrorDict()
        errors[NON_FIELD_ERRORS] = ErrorList([
            ValidationError(_('Your feedback could not be sent, please try again later'))
        ])
        return self.make_response(errors=errors)

    def form_invalid(self, form):
        return self.make_response(referer=form.cleaned_data.get('referer'), errors=form.errors)

    def form_valid(self, form):
        try:
            form.submit_ticket(self.request, self.subject, self.tags, self.ticket_template_name)
        except HTTPError:
            form.add_error(NON_FIELD_ERRORS, _('Your feedback could not be sent, please try again later'))
        return self.make_response(referer=form.cleaned_data.get('referer'))
