import logging
import math

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext, gettext_lazy as _, ngettext_lazy
from django.views.generic.edit import FormView

from mtp_common.api import api_errors_to_messages, retrieve_all_pages_for_path
from mtp_common.auth import api_client
from mtp_common.auth.exceptions import HttpNotFoundError, HttpClientError
from mtp_common.user_admin.forms import UserUpdateForm, AcceptRequestForm

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
    session = api_client.get_api_session(request)
    response = session.get(
        'users/',
        params={'limit': page_size, 'offset': (page - 1) * page_size}
    ).json()
    users = response.get('results', [])
    account_requests = retrieve_all_pages_for_path(session, 'requests/')
    for account_request in account_requests:
        account_request['created'] = parse_datetime(account_request['created'])
    context = {
        'can_delete': request.user.has_perm('auth.delete_user'),
        'locked_users_exist': any(user['is_locked_out'] for user in users),
        'users': users,
        'page': page,
        'page_count': int(math.ceil(response.get('count', 0) / page_size)),
        'account_requests': account_requests,
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
            api_client.get_api_session(request).delete(
                'users/{username}/'.format(username=username)
            )

            admin_username = request.user.user_data.get('username', 'Unknown')
            logger.info('Admin %(admin_username)s disabled user %(username)s' % {
                'admin_username': admin_username,
                'username': username,
            }, extra={
                'elk_fields': {
                    '@fields.username': admin_username,
                }
            })
            context['page_title'] = _('User account ‘%(username)s’ disabled') % {'username': username}
            return render(request, 'mtp_common/user_admin/deleted.html', context=context)
        except HttpClientError as e:
            api_errors_to_messages(request, e, gettext('This user could not be disabled'))
            return redirect(reverse('list-users'))

    try:
        user = api_client.get_api_session(request).get(
            'users/{username}/'.format(username=username)
        ).json()
        context['user'] = user
        context['page_title'] = _('Disable user account ‘%(username)s’') % {'username': user['username']}
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
            api_client.get_api_session(request).patch(
                'users/{username}/'.format(username=username),
                json={'is_active': True}
            )

            admin_username = request.user.user_data.get('username', 'Unknown')
            logger.info('Admin %(admin_username)s enabled user %(username)s' % {
                'admin_username': admin_username,
                'username': username,
            }, extra={
                'elk_fields': {
                    '@fields.username': admin_username,
                }
            })
            context['page_title'] = _('User account ‘%(username)s’ enabled') % {'username': username}
            return render(request, 'mtp_common/user_admin/undeleted.html', context=context)
        except HttpClientError as e:
            api_errors_to_messages(request, e, gettext('This user could not be enabled'))
            return redirect(reverse('list-users'))

    try:
        user = api_client.get_api_session(request).get(
            'users/{username}/'.format(username=username)
        ).json()
        context['user'] = user
        context['page_title'] = _('Enable user account ‘%(username)s’') % {'username': user['username']}
        return render(request, 'mtp_common/user_admin/undelete.html', context=context)
    except HttpNotFoundError:
        raise Http404


@login_required
@permission_required('auth.change_user', raise_exception=True)
@ensure_compatible_admin
def unlock_user(request, username):
    try:
        api_client.get_api_session(request).patch(
            'users/{username}/'.format(username=username),
            json={'is_locked_out': False}
        )

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
        if form.create:
            page_title = _('User account ‘%(username)s’ created')
        else:
            page_title = _('User account ‘%(username)s’ edited')
        context = {
            'user': form.cleaned_data,
            'page_title': page_title % {'username': form.cleaned_data.get('username')},
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
        context_data = super().get_context_data(page_title=_('Create a new user'), **kwargs)

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
            response = api_client.get_api_session(self.request).get(
                'users/{username}/'.format(username=username)
            ).json()
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

    def get_context_data(self, **kwargs):
        page_title = _('Edit user ‘%(username)s’') % {'username': self.kwargs['username']}
        return super().get_context_data(page_title=page_title, **kwargs)


class SignUpView(FormView):
    template_name = 'mtp_common/user_admin/sign-up.html'
    has_role_template_name = 'mtp_common/user_admin/sign-up-has-role.html'
    has_other_roles_template_name = 'mtp_common/user_admin/sign-up-has-other-roles.html'
    success_template_name = 'mtp_common/user_admin/sign-up-success.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', None) or '/')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['page_title'] = _('Request access')
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    def form_valid(self, form):
        return self.response_class(
            request=self.request,
            template=[self.success_template_name],
            context=self.get_context_data(),
            using=self.template_engine,
        )

    def form_invalid(self, form):
        if form.error_conditions.get('condition') == 'user-exists':
            return self.confirm_account_changes(form)
        return super().form_invalid(form)

    def confirm_account_changes(self, form):
        context = self.get_context_data(form=form)
        requested_role = form.cleaned_data['role']
        current_roles = form.error_conditions['roles']
        has_requested_role = next(filter(lambda role: role['role'] == requested_role, current_roles), None)
        if has_requested_role:
            context.update(
                page_title=_('You already have access to this service'),
                login_url=has_requested_role['login_url'],
            )
            template_name = self.has_role_template_name
        else:
            login_urls = {
                role['application']: role['login_url']
                for role in current_roles
            }
            login_urls = [
                (application, login_url)
                for application, login_url in login_urls.items()
            ]
            context.update(
                page_title=ngettext_lazy(
                    'You already have access to another service',
                    'You already have access to other services',
                    len(login_urls)
                ),
                login_urls=login_urls,
            )
            template_name = self.has_other_roles_template_name
        return self.response_class(
            request=self.request,
            template=[template_name],
            context=context,
            using=self.template_engine,
        )


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required(['auth.add_user', 'auth.change_user'], raise_exception=True), name='dispatch')
@method_decorator(ensure_compatible_admin, name='dispatch')
class AcceptRequestView(FormView):
    template_name = 'mtp_common/user_admin/accept-request.html'
    form_class = AcceptRequestForm
    success_url = reverse_lazy('list-users')

    def get_form(self, form_class=None):
        try:
            return super().get_form(form_class)
        except HttpNotFoundError:
            raise Http404

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(
            request=self.request,
            account_request=self.kwargs['account_request'],
        )
        return form_kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        account_request = context_data['form'].account_request
        account_request.update(
            created=parse_datetime(account_request['created']),
            full_name='%s %s' % (account_request['first_name'], account_request['last_name']),
        )
        context_data.update(
            breadcrumbs_back=self.success_url,
            account_request=account_request,
        )
        return context_data

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, gettext('New user request accepted'))
        return response


@login_required
@permission_required('auth.change_user', raise_exception=True)
@ensure_compatible_admin
def decline_request(request, account_request):
    response = api_client.get_api_session(request).delete('requests/%s/' % account_request)
    if response.status_code == 204:
        messages.success(request, gettext('New user request was declined'))
    else:
        messages.error(request, gettext('New user request could not be declined'))
    return redirect(AcceptRequestView.success_url)
