from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic.edit import FormView
from moj_auth import api_client
from mtp_utils.api import retrieve_all_pages
from slumber.exceptions import HttpNotFoundError

from .forms import UserUpdateForm


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
            return render(request, 'mtp_user_admin/deleted.html', {'username': username})
        except HttpNotFoundError:
            raise Http404
    else:
        return render(request, 'mtp_user_admin/delete.html', {'username': username})


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.add_user', raise_exception=True), name='dispatch')
class UserCreationView(FormView):
    template_name = 'mtp_user_admin/create.html'
    form_class = UserUpdateForm
    success_url = reverse_lazy('list-users')

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        form_kwargs['create'] = True
        return form_kwargs


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.change_user', raise_exception=True), name='dispatch')
class UserUpdateView(FormView):
    template_name = 'mtp_user_admin/update.html'
    form_class = UserUpdateForm
    success_url = reverse_lazy('list-users')

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

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs
