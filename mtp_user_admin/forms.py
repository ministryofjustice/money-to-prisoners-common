import json

from django import forms
from django.utils.translation import ugettext_lazy as _
from moj_auth import api_client
from slumber.exceptions import HttpClientError


class UserCreationForm(forms.Form):
    error_messages = {
        'generic': _('The service is currently unavailable.')
    }

    username = forms.CharField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.CharField()
    is_admin = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.is_valid():
            data = {
                'username': self.cleaned_data['username'],
                'first_name': self.cleaned_data['first_name'],
                'last_name': self.cleaned_data['last_name'],
                'email': self.cleaned_data['email'],
                'is_admin': self.cleaned_data['is_admin'],
            }
            try:
                api_client.get_connection(self.request).users().post(data)
            except HttpClientError as e:
                try:
                    response_body = json.loads(e.content.decode('utf-8'))
                    for field in response_body['errors']:
                        for error in response_body['errors'][field]:
                            self.add_error(field, error)
                except (ValueError, KeyError):
                    raise forms.ValidationError(self.error_messages['service_unavailable'])
