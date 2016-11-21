import json
import logging

from django import forms
from django.utils.translation import gettext_lazy as _
from form_error_reporting import GARequestErrorReportingMixin
from slumber.exceptions import HttpClientError

from mtp_common.auth import api_client

logger = logging.getLogger('mtp')


class UserUpdateForm(GARequestErrorReportingMixin, forms.Form):
    username = forms.CharField(label=_('Username'), disabled=True,
                               help_text=_('Enter the user’s Quantum ID'))
    first_name = forms.CharField(label=_('First name'))
    last_name = forms.CharField(label=_('Last name'))
    email = forms.EmailField(label=_('Email'))
    user_admin = forms.BooleanField(label=_('Give access to manage other users'), required=False)

    error_messages = {
        'generic': _('This service is currently unavailable')
    }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.create = kwargs.pop('create', False)
        super().__init__(*args, **kwargs)
        if self.create:
            self.fields['username'].disabled = False

    def clean(self):
        if self.is_valid():
            data = {
                'first_name': self.cleaned_data['first_name'],
                'last_name': self.cleaned_data['last_name'],
                'email': self.cleaned_data['email'],
                'user_admin': self.cleaned_data['user_admin'],
            }
            try:
                admin_username = self.request.user.user_data.get('username', 'Unknown')

                if self.create:
                    data['username'] = self.cleaned_data['username']
                    api_client.get_connection(self.request).users().post(data)

                    logger.info('Admin %(admin_username)s created user %(username)s' % {
                        'admin_username': admin_username,
                        'username': data['username'],
                    }, extra={
                        'elk_fields': {
                            '@fields.username': admin_username,
                        }
                    })
                else:
                    username = self.initial['username']
                    api_client.get_connection(self.request).users(username).patch(data)

                    logger.info('Admin %(admin_username)s edited user %(username)s' % {
                        'admin_username': admin_username,
                        'username': username,
                    }, extra={
                        'elk_fields': {
                            '@fields.username': admin_username,
                        }
                    })
            except HttpClientError as e:
                try:
                    response_body = json.loads(e.content.decode('utf-8'))
                    for field, errors in response_body.items():
                        if isinstance(errors, list):
                            for error in errors:
                                self.add_error(field, error)
                        else:
                            self.add_error(field, errors)
                except (AttributeError, ValueError, KeyError):
                    raise forms.ValidationError(self.error_messages['generic'])
        return self.cleaned_data
