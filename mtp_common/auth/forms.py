import json
import logging

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from form_error_reporting import GARequestErrorReportingMixin
from requests.exceptions import ConnectionError

from . import api_client
from .exceptions import Unauthorized, Forbidden, HttpClientError, HttpNotFoundError

logger = logging.getLogger('mtp')

RESET_CODE_PARAM = 'reset_code'


class AuthenticationForm(GARequestErrorReportingMixin, forms.Form):
    """
    Authentication form used for authenticating users during the login process.
    """
    username = forms.CharField(label=_('Username'), max_length=30)
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _('You’ve entered an incorrect username and/or password'),
        'application_inaccessible': _('You don’t have access to this application'),
        'connection_error': _('This service is currently unavailable'),
        'lockout_imminent': _(
            'You’ll be LOCKED OUT if you enter another incorrect username '
            'and/or password'
        ),
        'locked_out': _(
            'You’ve been locked out of this account. '
            'Please wait 10 minutes, then click on ‘Forgotten your password’.'
        ),
    }

    def __init__(self, request=None, **kwargs):
        self.request = request
        self.user_cache = None
        super(AuthenticationForm, self).__init__(**kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                self.user_cache = authenticate(
                    username=username, password=password
                )
                # if authenticate returns None it means that the
                # credentials were wrong
                if self.user_cache is None:
                    raise Unauthorized

            except ConnectionError:
                # in case of problems connecting to the api server
                raise forms.ValidationError(
                    self.error_messages['connection_error'],
                    code='connection_error',
                )
            except Forbidden:
                raise forms.ValidationError(
                    self.error_messages['application_inaccessible'],
                    code='application_inaccessible',
                )
            except Unauthorized as e:
                try:
                    response_body = json.loads(e.content.decode('utf-8'))
                    if response_body['error'] == 'lockout_imminent':
                        raise forms.ValidationError(
                            self.error_messages['lockout_imminent'],
                            code='lockout_imminent',
                        )
                    elif response_body['error'] == 'locked_out':
                        raise forms.ValidationError(
                            self.error_messages['locked_out'],
                            code='locked_out',
                        )
                except (AttributeError, ValueError, KeyError):
                    pass
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )

        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class PasswordChangeForm(GARequestErrorReportingMixin, forms.Form):
    """
    A form that lets a user change their password by entering their old
    password.
    """
    error_messages = {
        'password_mismatch': _('You’ve entered different passwords'),
        'generic': _('This service is currently unavailable'),
    }
    old_password = forms.CharField(label=_('Old password'),
                                   widget=forms.PasswordInput)
    new_password = forms.CharField(label=_('New password'),
                                   widget=forms.PasswordInput)
    new_password_confirmation = forms.CharField(label=_('New password confirmation'),
                                                widget=forms.PasswordInput)

    def __init__(self, request=None, user=None, *args, **kwargs):
        self.request = request
        self.user = user
        super(PasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_new_password_confirmation(self):
        password1 = self.cleaned_data.get('new_password')
        password2 = self.cleaned_data.get('new_password_confirmation')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def clean(self):
        if self.is_valid():
            old_password = self.cleaned_data.get('old_password')
            new_password = self.cleaned_data.get('new_password')
            try:
                api_client.get_api_session(self.request).post(
                    'change_password/',
                    json={'old_password': old_password, 'new_password': new_password}
                )
            except HttpClientError as e:
                try:
                    response_body = json.loads(e.content.decode('utf-8'))
                    for field in response_body['errors']:
                        for error in response_body['errors'][field]:
                            self.add_error(field, error)
                except Exception:
                    logger.exception('Could not display password change error')
                    raise forms.ValidationError(self.error_messages['generic'])


class ResetPasswordForm(GARequestErrorReportingMixin, forms.Form):
    error_messages = {
        'generic': _('This service is currently unavailable')
    }
    username = forms.CharField(label=_('Username or email address'))

    def __init__(self, password_change_url, request=None, *args, **kwargs):
        self.password_change_url = password_change_url
        self.request = request
        super(ResetPasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.is_valid():
            username = self.cleaned_data.get('username')
            try:
                api_client.get_unauthenticated_session().post(
                    'reset_password/',
                    json={
                        'username': username,
                        'create_password': {
                            'password_change_url': settings.SITE_URL + str(self.password_change_url),
                            'reset_code_param': RESET_CODE_PARAM
                        }
                    }
                )
            except HttpClientError as e:
                try:
                    response_body = json.loads(e.content.decode('utf-8'))
                    for field in response_body['errors']:
                        for error in response_body['errors'][field]:
                            self.add_error(field, error)
                except Exception:
                    logger.exception('Could not display password change error')
                    raise forms.ValidationError(self.error_messages['generic'])


class PasswordChangeWithCodeForm(GARequestErrorReportingMixin, forms.Form):
    """
    A form that lets a user change their password if they have a reset code.
    """
    error_messages = {
        'code_expired': _('This link for resetting your password has expired'),
        'password_mismatch': _('You’ve entered different passwords'),
        'generic': _('This service is currently unavailable'),
    }
    reset_code = forms.CharField(label=_('Reset code'),
                                 widget=forms.HiddenInput)
    new_password = forms.CharField(label=_('New password'),
                                   widget=forms.PasswordInput)
    new_password_confirmation = forms.CharField(label=_('New password confirmation'),
                                                widget=forms.PasswordInput)

    def __init__(self, reset_code=None, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        if reset_code:
            self.fields['reset_code'].initial = reset_code

    def clean_new_password_confirmation(self):
        password1 = self.cleaned_data.get('new_password')
        password2 = self.cleaned_data.get('new_password_confirmation')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def clean(self):
        if self.is_valid():
            code = self.cleaned_data.get('reset_code')
            new_password = self.cleaned_data.get('new_password')
            try:
                api_client.get_api_session(self.request).post(
                    '/change_password/{code}/'.format(code=code),
                    json={'new_password': new_password}
                )
            except HttpNotFoundError:
                raise forms.ValidationError(self.error_messages['code_expired'])
            except HttpClientError as e:
                try:
                    response_body = json.loads(e.content.decode('utf-8'))
                    for field in response_body['errors']:
                        for error in response_body['errors'][field]:
                            self.add_error(field, error)
                except Exception:
                    logger.exception('Could not display password change error')
                    raise forms.ValidationError(self.error_messages['generic'])
