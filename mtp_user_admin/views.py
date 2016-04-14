import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext, ngettext
from django.views.generic.edit import FormView
from moj_auth import api_client
from mtp_utils.api import retrieve_all_pages
from slumber.exceptions import HttpNotFoundError, HttpClientError

from .forms import UserUpdateForm

logger = logging.getLogger('mtp')


@login_required
@permission_required('auth.change_user', raise_exception=True)
def list_users(request):
    users = retrieve_all_pages(
        api_client.get_connection(request).users.get
    )
    return render(request, 'mtp_user_admin/list.html', {'users': users})


@login_required
@permission_required('auth.delete_user', raise_exception=True)
def delete_user(request, username):
    if request.method == 'POST':
        try:
            api_client.get_connection(request).users(username).delete()

            admin_username = request.user.user_data.get('username', 'Unknown')
            logger.info('Admin %(admin_username)s deleted user %(username)s' % {
                'admin_username': admin_username,
                'username': username,
            }, extra={
                'elk_fields': {
                    '@fields.username': admin_username,
                }
            })

            return render(request, 'mtp_user_admin/deleted.html', {'username': username})
        except HttpClientError as e:
            try:
                response_body = json.loads(e.content.decode('utf-8'))
                for field, errors in response_body.items():
                    if isinstance(errors, list):
                        for error in errors:
                            messages.error(request, error)
                    else:
                        messages.error(request, errors)
            except (AttributeError, ValueError, KeyError):
                messages.error(request, gettext('This user could not be deleted'))
            return redirect(reverse('list-users'))

    try:
        user = api_client.get_connection(request).users(username).get()
        return render(request, 'mtp_user_admin/delete.html', {'user': user})
    except HttpNotFoundError:
        raise Http404


class UserFormView(FormView):
    template_name = 'mtp_user_admin/update.html'
    form_class = UserUpdateForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    def form_valid(self, form):
        return render(self.request, 'mtp_user_admin/saved.html',
                      {'user': form.cleaned_data, 'create': form.create})


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.add_user', raise_exception=True), name='dispatch')
class UserCreationView(UserFormView):

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['create'] = True
        return form_kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        # TODO: this note only applies to cashbook; we need a way to pass it in from client apps
        prison_count = len(self.request.user.user_data.get('prisons', []))
        if prison_count > 0:
            context_data['permissions_note'] = ngettext(
                'The new user will have access to the same prison as you do.',
                'The new user will have access to the same prisons as you do.',
                prison_count
            ) % {
                'prison_count': prison_count
            }
        else:
            context_data['permissions_note'] = gettext('The new user will not have access to manage any prisons.')

        return context_data


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.change_user', raise_exception=True), name='dispatch')
class UserUpdateView(UserFormView):

    def get_initial(self):
        username = self.kwargs['username']
        try:
            response = api_client.get_connection(self.request).users(username).get()
            return {
                'username': response.get('username', ''),
                'first_name': response.get('first_name', ''),
                'last_name': response.get('last_name', ''),
                'email': response.get('email', ''),
                'user_admin': response.get('user_admin', False),
            }
        except HttpNotFoundError:
            raise Http404
