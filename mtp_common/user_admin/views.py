import logging
import math

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic.edit import FormView
from slumber.exceptions import HttpNotFoundError, HttpClientError

from mtp_common.api import api_errors_to_messages
from mtp_common.auth import api_client
from mtp_common.user_admin.forms import UserUpdateForm

logger = logging.getLogger('mtp')


def make_breadcrumbs(section_title):
    return [
        {'name': _('Home'), 'url': '/'},
        {'name': _('Manage user accounts'), 'url': reverse('list-users')},
        {'name': section_title}
    ]


def ensure_compatible_admin(view):
    """
    Ensures that the user is in exactly one role.
    Other checks could be added, such as requiring one prison if in prison-clerk role.
    """

    def wrapper(request, *args, **kwargs):
        user_roles = request.user.user_data.get('roles', [])
        if len(user_roles) != 1:
            context = {
                'message': 'I need to be able to manage user accounts. '
                           'My username is %s' % request.user.username
            }
            return render(request, 'mtp_common/user_admin/incompatible-admin.html', context=context)
        return view(request, *args, **kwargs)

    return wrapper


@login_required
@permission_required('auth.change_user', raise_exception=True)
@ensure_compatible_admin
def list_users(request):
    page_size = 20
    try:
        page = int(request.GET['page'])
        if page < 1:
            raise ValueError
    except (KeyError, ValueError):
        page = 1
    response = api_client.get_connection(request).users.get(limit=page_size, offset=(page - 1) * page_size)
    users = response.get('results', [])
    context = {
        'can_delete': request.user.has_perm('auth.delete_user'),
        'locked_users_exist': any(user['is_locked_out'] for user in users),
        'users': users,
        'page': page,
        'page_count': int(math.ceil(response.get('count', 0) / page_size)),
    }
    return render(request, 'mtp_common/user_admin/list.html', context=context)


@login_required
@permission_required('auth.delete_user', raise_exception=True)
@ensure_compatible_admin
def delete_user(request, username):
    context = {
        'breadcrumbs': make_breadcrumbs(_('Disable user')),
    }
    if request.method == 'POST':
        try:
            api_client.get_connection(request).users(username).delete()

            admin_username = request.user.user_data.get('username', 'Unknown')
            logger.info('Admin %(admin_username)s disabled user %(username)s' % {
                'admin_username': admin_username,
                'username': username,
            }, extra={
                'elk_fields': {
                    '@fields.username': admin_username,
                }
            })
            context['username'] = username
            return render(request, 'mtp_common/user_admin/deleted.html', context=context)
        except HttpClientError as e:
            api_errors_to_messages(request, e, gettext('This user could not be disabled'))
            return redirect(reverse('list-users'))

    try:
        user = api_client.get_connection(request).users(username).get()
        context['user'] = user
        return render(request, 'mtp_common/user_admin/delete.html', context=context)
    except HttpNotFoundError:
        raise Http404


@login_required
@permission_required('auth.delete_user', raise_exception=True)
@ensure_compatible_admin
def undelete_user(request, username):
    context = {
        'breadcrumbs': make_breadcrumbs(_('Enable user')),
    }
    if request.method == 'POST':
        try:
            api_client.get_connection(request).users(username).patch({
                'is_active': True,
            })

            admin_username = request.user.user_data.get('username', 'Unknown')
            logger.info('Admin %(admin_username)s enabled user %(username)s' % {
                'admin_username': admin_username,
                'username': username,
            }, extra={
                'elk_fields': {
                    '@fields.username': admin_username,
                }
            })
            context['username'] = username
            return render(request, 'mtp_common/user_admin/undeleted.html', context=context)
        except HttpClientError as e:
            api_errors_to_messages(request, e, gettext('This user could not be enabled'))
            return redirect(reverse('list-users'))

    try:
        user = api_client.get_connection(request).users(username).get()
        context['user'] = user
        return render(request, 'mtp_common/user_admin/undelete.html', context=context)
    except HttpNotFoundError:
        raise Http404


@login_required
@permission_required('auth.change_user', raise_exception=True)
@ensure_compatible_admin
def unlock_user(request, username):
    try:
        api_client.get_connection(request).users(username).patch({
            'is_locked_out': False,
        })

        admin_username = request.user.user_data.get('username', 'Unknown')
        logger.info('Admin %(admin_username)s removed lock-out for user %(username)s' % {
            'admin_username': admin_username,
            'username': username,
        }, extra={
            'elk_fields': {
                '@fields.username': admin_username,
            }
        })
        messages.success(request, gettext('Unlocked user ‘%(username)s’, they can now log in again') % {
            'username': username,
        })
    except HttpClientError as e:
        api_errors_to_messages(request, e, gettext('This user could not be enabled'))
    return redirect(reverse('list-users'))


class UserFormView(FormView):
    title = _('Edit user')
    template_name = 'mtp_common/user_admin/update.html'
    form_class = UserUpdateForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['breadcrumbs'] = make_breadcrumbs(self.title)
        return context_data

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    def form_valid(self, form):
        context = {
            'user': form.cleaned_data,
            'create': form.create,
            'breadcrumbs': make_breadcrumbs(self.title),
        }
        return render(self.request, 'mtp_common/user_admin/saved.html', context=context)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.add_user', raise_exception=True), name='dispatch')
@method_decorator(ensure_compatible_admin, name='dispatch')
class UserCreationView(UserFormView):
    title = _('Add user')

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['create'] = True
        return form_kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        prisons = self.request.user.user_data.get('prisons', [])
        if prisons:
            prisons = [prison['name'] for prison in prisons]
            if len(prisons) > 1:
                prisons = gettext('%(prison_list)s and %(prison)s') % {
                    'prison_list': ', '.join(prisons[:-1]),
                    'prison': prisons[-1],
                }
            else:
                prisons = prisons[0]
            permissions_note = gettext('The new user will be based at %(prison_list)s.') % {
                'prison_list': prisons,
            }
        else:
            permissions_note = gettext('The new user will not be based at a specific prison.')
        context_data['permissions_note'] = permissions_note

        return context_data


class IncompatibleUser(Exception):
    pass


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.change_user', raise_exception=True), name='dispatch')
@method_decorator(ensure_compatible_admin, name='dispatch')
class UserUpdateView(UserFormView):
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except IncompatibleUser:
            admin_username = request.user.username
            target_username = self.kwargs.get('username')
            context = {
                'target_username': target_username,
                'message': 'My username is %s. '
                           'I need to be able to edit the account for %s' % (admin_username, target_username),
            }
            return render(request, 'mtp_common/user_admin/incompatible-user.html', context=context)

    def get_initial(self):
        username = self.kwargs['username']
        try:
            response = api_client.get_connection(self.request).users(username).get()
            initial = {
                'username': response.get('username', ''),
                'first_name': response.get('first_name', ''),
                'last_name': response.get('last_name', ''),
                'email': response.get('email', ''),
                'user_admin': response.get('user_admin', False),
            }
            roles = response.get('roles', [])
            if len(roles) == 1:
                initial['role'] = roles[0]
            else:
                raise IncompatibleUser
            return initial
        except HttpNotFoundError:
            raise Http404
