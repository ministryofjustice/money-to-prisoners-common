import json
import logging

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from form_error_reporting import GARequestErrorReportingMixin

from mtp_common.auth import api_client
from mtp_common.auth.exceptions import HttpClientError

logger = logging.getLogger('mtp')


class ApiForm(GARequestErrorReportingMixin, forms.Form):
    error_messages = {
        'generic': _('This service is currently unavailable')
    }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    @property
    def api_session(self):
        return api_client.get_api_session(self.request)

    def api_validation_error(self, error):
        try:
            response_body = json.loads(error.content.decode('utf-8'))
            for field, errors in response_body.items():
                if field in ('__all__', 'non_field_errors', 'detail'):
                    field = None
                if isinstance(errors, list):
                    for error in errors:
                        self.add_error(field, error)
                else:
                    self.add_error(field, errors)
        except (AttributeError, ValueError, KeyError):
            logger.exception('api returned unexpected error response')
            raise forms.ValidationError(self.error_messages['generic'])


class UserUpdateForm(ApiForm):
    username = forms.CharField(label=_('Username'), disabled=True,
                               help_text=_('Enter the user’s Quantum ID'))
    first_name = forms.CharField(label=_('First name'))
    last_name = forms.CharField(label=_('Last name'))
    email = forms.EmailField(label=_('Email'))
    role = forms.ChoiceField(label=_('Role'), error_messages={
        'required': _('Please choose user’s role'),
    })
    user_admin = forms.BooleanField(label=_('Give access to manage other users'), required=False)

    def __init__(self, *args, **kwargs):
        self.create = kwargs.pop('create', False)
        super().__init__(*args, **kwargs)
        if self.request.user.username.lower() == kwargs.get('initial', {}).get('username', '').lower():
            del self.fields['role']
            del self.fields['user_admin']
        else:
            response = self.api_session.get('roles/', params={'managed': 1})
            managed_roles = response.json().get('results', [])
            initial_role = None
            role_choices = []
            for role in managed_roles:
                role_choices.append((role['name'], role['application']['name']))
                if role['application']['client_id'] == settings.API_CLIENT_ID:
                    initial_role = role['name']
            role_field = self.fields['role']
            role_field.initial = initial_role
            role_field.choices = role_choices
        if self.create:
            self.fields['username'].disabled = False

    def clean(self):
        if self.is_valid():
            data = {
                'first_name': self.cleaned_data['first_name'],
                'last_name': self.cleaned_data['last_name'],
                'email': self.cleaned_data['email'],
            }
            if 'user_admin' in self.cleaned_data:
                data['user_admin'] = self.cleaned_data['user_admin']
            if 'role' in self.cleaned_data:
                data['role'] = self.cleaned_data['role']
            try:
                admin_username = self.request.user.user_data.get('username', 'Unknown')

                if self.create:
                    data['username'] = self.cleaned_data['username']
                    self.api_session.post('users/', json=data)

                    logger.info('Admin %(admin_username)s created user %(username)s', {
                        'admin_username': admin_username,
                        'username': data['username'],
                    }, extra={
                        'elk_fields': {
                            '@fields.username': admin_username,
                        }
                    })
                else:
                    username = self.initial['username']
                    self.api_session.patch(
                        'users/{username}/'.format(username=username), json=data
                    )

                    logger.info('Admin %(admin_username)s edited user %(username)s', {
                        'admin_username': admin_username,
                        'username': username,
                    }, extra={
                        'elk_fields': {
                            '@fields.username': admin_username,
                        }
                    })
            except HttpClientError as e:
                self.api_validation_error(e)
        return super().clean()


class SignUpForm(ApiForm):
    first_name = forms.CharField(label=_('First name'))
    last_name = forms.CharField(label=_('Last name'))
    username = forms.CharField(label=_('Username'), help_text=_('Enter your Quantum ID'))
    email = forms.EmailField(label=_('Email'))
    reason = forms.CharField(label=_('Reason for needing an account'), required=False)
    role = forms.ChoiceField(label=_('Role'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_conditions = {}

    @property
    def api_session(self):
        return api_client.get_unauthenticated_session()

    @property
    def payload(self):
        payload = {
            key: self.cleaned_data[key]
            for key in self.fields.keys()
        }
        if 'change-role' in self.request.POST:
            payload['change-role'] = self.request.POST['change-role']
        return payload

    def clean(self):
        if self.is_valid():
            try:
                response = self.api_session.post('requests/', data=self.payload)
                if response.status_code != 201:
                    logger.error('Sign up api error: %r', {'api_response': response.content})
                    raise forms.ValidationError(self.error_messages['generic'])
            except HttpClientError as e:
                self.api_validation_error(e)
        return super().clean()

    def add_error(self, field, error):
        if field == '__mtp__':
            self.error_conditions = error
        else:
            super().add_error(field, error)


class AcceptRequestForm(ApiForm):
    user_admin = forms.BooleanField(label=_('Give access to manage other users'), required=False)

    def __init__(self, *args, **kwargs):
        self.url = 'requests/%s/' % kwargs.pop('account_request')
        super().__init__(*args, **kwargs)
        self.account_request = self.api_session.get(self.url).json()

    def clean(self):
        if self.is_valid():
            try:
                user_admin = str(self.cleaned_data.get('user_admin'))
                response = self.api_session.patch(self.url, data={'user_admin': user_admin})
                if response.status_code != 200:
                    logger.error('Accept account request api error: %r', {'api_response': response.content})
                    raise forms.ValidationError(self.error_messages['generic'])
            except HttpClientError as e:
                self.api_validation_error(e)
        return super().clean()
