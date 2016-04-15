from django import forms
from django.core.validators import EmailValidator
from django.utils.translation import ugettext_lazy as _


def replace_default_error_messages():
    """
    Replace Django's generic error messages with MTP-specific versions
    NB: avoid trailing full stops
    """
    forms.CharField.default_error_messages['required'] = _('This field is required')
    EmailValidator.message = _('Enter a valid email address')
