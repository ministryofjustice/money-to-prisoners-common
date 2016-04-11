import json

from django import forms
from django.utils.translation import ugettext_lazy as _
from moj_auth import api_client
from slumber.exceptions import HttpClientError


class UserUpdateForm(forms.Form):
    error_messages = {
        'generic': _('The service is currently unavailable.')
    }

    username = forms.CharField(label=_('Username'), disabled=True)
    first_name = forms.CharField(label=_('First name'))
    last_name = forms.CharField(label=_('Last name'))
    email = forms.EmailField(label=_('Email'))
    user_admin = forms.BooleanField(label=_('Grant access to create and edit users'), required=False)

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
                if self.create:
                    data['username'] = self.cleaned_data['username']
                    api_client.get_connection(self.request).users().post(data)
                else:
                    username = self.initial['username']
                    api_client.get_connection(self.request).users(username).patch(data)
            except HttpClientError as e:
                try:
                    response_body = json.loads(e.content.decode('utf-8'))
                    for field in response_body:
                        for error in response_body[field]:
                            self.add_error(field, error)
                except (ValueError, KeyError):
                    raise forms.ValidationError(self.error_messages['generic'])
        return self.cleaned_data
