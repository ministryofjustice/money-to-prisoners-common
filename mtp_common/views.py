from django.views import defaults
from zendesk_tickets.forms import EmailTicketForm
from zendesk_tickets.views import TicketView, TicketSentView


def page_not_found(request, exception, template_name='mtp_common/errors/404.html'):
    return defaults.page_not_found(request, exception, template_name)


def server_error(request, template_name='mtp_common/errors/500.html'):
    return defaults.server_error(request, template_name)


def bad_request(request, exception, template_name='mtp_common/errors/400.html'):
    return defaults.bad_request(request, exception, template_name)


class GetHelpView(TicketView):
    form_class = EmailTicketForm
    base_template_name = 'base.html'
    template_name = 'mtp_common/feedback/submit_feedback.html'

    def get_initial(self):
        initial = super().get_initial()
        if not self.request.user.is_anonymous and self.request.user.email:
            initial['contact_email'] = self.request.user.email
        return initial

    def get_context_data(self, **kwargs):
        kwargs['base_template_name'] = self.base_template_name
        context = super().get_context_data(**kwargs)
        if 'return_to' in context:
            context['breadcrumbs_back'] = context['return_to']
        return context


class GetHelpSuccessView(TicketSentView):
    base_template_name = 'base.html'
    template_name = 'mtp_common/feedback/success.html'

    def get_context_data(self, **kwargs):
        kwargs['base_template_name'] = self.base_template_name
        context = super().get_context_data(**kwargs)
        if 'return_to' in context:
            context['breadcrumbs_back'] = context['return_to']
        return context
