from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from . import login as auth_login, logout as auth_logout
from .forms import (
    AuthenticationForm, PasswordChangeForm, ResetPasswordForm,
    PasswordChangeWithCodeForm, RESET_CODE_PARAM
)


def make_breadcrumbs(section_title):
    return [
        {'name': _('Home'), 'url': '/'},
        {'name': section_title},
    ]


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name=None,
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.POST.get(
        redirect_field_name,
        request.GET.get(redirect_field_name, '')
    )

    def get_redirect_to():
        # Ensure the user-originating redirection url is safe.
        if not is_safe_url(url=redirect_to, host=request.get_host()):
            return resolve_url(settings.LOGIN_REDIRECT_URL)
        return redirect_to

    if request.user.is_authenticated:
        return HttpResponseRedirect(get_redirect_to())

    if request.method == "POST":
        form = authentication_form(request=request, data=request.POST)
        if form.is_valid():

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            return HttpResponseRedirect(get_redirect_to())
    else:
        form = authentication_form(request=request)

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)


def logout(request, template_name=None,
           next_page=None,
           redirect_field_name=REDIRECT_FIELD_NAME,
           current_app=None, extra_context=None):
    """
    Logs out the user.
    """
    auth_logout(request)

    if next_page is not None:
        next_page = resolve_url(next_page)

    if (redirect_field_name in request.POST or
            redirect_field_name in request.GET):
        next_page = request.POST.get(redirect_field_name,
                                     request.GET.get(redirect_field_name))
        # Security check -- don't allow redirection to a different host.
        if not is_safe_url(url=next_page, host=request.get_host()):
            next_page = request.path

    if next_page:
        # Redirect to this page until the session has been cleared.
        return HttpResponseRedirect(next_page)

    current_site = get_current_site(request)
    context = {
        'site': current_site,
        'site_name': current_site.name,
        'title': _('Logged out')
    }
    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)


@sensitive_post_parameters()
@csrf_protect
@login_required
def password_change(request,
                    template_name=None,
                    cancel_url=None,
                    post_change_redirect=None,
                    password_change_form=PasswordChangeForm,
                    extra_context=None):
    cancel_url = resolve_url(cancel_url or '/')
    if post_change_redirect is None:
        post_change_redirect = reverse('password_change_done')
    else:
        post_change_redirect = resolve_url(post_change_redirect)
    if request.method == 'POST':
        form = password_change_form(user=request.user, request=request, data=request.POST)
        if form.is_valid():
            return HttpResponseRedirect(post_change_redirect)
    else:
        form = password_change_form(user=request.user, request=request)
    context = {
        'form': form,
        'cancel_url': cancel_url,
        'breadcrumbs': make_breadcrumbs(_('Change password')),
    }
    context.update(extra_context or {})
    return TemplateResponse(request, template_name, context)


@sensitive_post_parameters()
@csrf_protect
def password_change_with_code(request,
                              template_name=None,
                              cancel_url=None,
                              post_change_redirect=None,
                              extra_context=None):
    cancel_url = resolve_url(cancel_url or '/')
    if post_change_redirect is None:
        post_change_redirect = reverse('password_change_done')
    else:
        post_change_redirect = resolve_url(post_change_redirect)
    if request.method == 'POST':
        form = PasswordChangeWithCodeForm(request=request, data=request.POST)
        if form.is_valid():
            return HttpResponseRedirect(post_change_redirect)
    else:
        reset_code = request.GET.get(RESET_CODE_PARAM)
        form = PasswordChangeWithCodeForm(reset_code=reset_code, request=request)
    context = {
        'form': form,
        'cancel_url': cancel_url,
        'breadcrumbs': make_breadcrumbs(_('Change password')),
    }
    context.update(extra_context or {})
    return TemplateResponse(request, template_name, context)


def password_change_done(request,
                         template_name=None,
                         cancel_url=None,
                         extra_context=None):
    cancel_url = resolve_url(cancel_url or '/')
    context = {
        'cancel_url': cancel_url,
        'breadcrumbs': make_breadcrumbs(_('Change password')),
    }
    context.update(extra_context or {})
    return TemplateResponse(request, template_name, context)


@csrf_protect
def reset_password(request,
                   password_change_url=None,
                   template_name=None,
                   cancel_url=None,
                   post_change_redirect=None,
                   reset_password_form=ResetPasswordForm,
                   extra_context=None):
    cancel_url = resolve_url(cancel_url or '/')
    if request.user.is_authenticated:
        return HttpResponseRedirect(cancel_url)
    if post_change_redirect is None:
        post_change_redirect = reverse('reset_password_done')
    else:
        post_change_redirect = resolve_url(post_change_redirect)
    if request.method == 'POST':
        form = reset_password_form(password_change_url, request=request, data=request.POST)
        if form.is_valid():
            return HttpResponseRedirect(post_change_redirect)
    else:
        form = reset_password_form(password_change_url, request=request)
    context = {
        'form': form,
        'cancel_url': cancel_url,
        'breadcrumbs': make_breadcrumbs(_('Reset password')),
    }
    context.update(extra_context or {})
    return TemplateResponse(request, template_name, context)


def reset_password_done(request,
                        template_name=None,
                        cancel_url=None,
                        extra_context=None):
    cancel_url = resolve_url(cancel_url or '/')
    if request.user.is_authenticated:
        return HttpResponseRedirect(cancel_url)
    context = {
        'cancel_url': cancel_url,
        'breadcrumbs': make_breadcrumbs(_('Reset password')),
    }
    context.update(extra_context or {})
    return TemplateResponse(request, template_name, context)
