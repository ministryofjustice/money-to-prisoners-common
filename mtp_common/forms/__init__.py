from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _


def replace_default_error_messages():
    """
    Replace Django's generic error messages with MTP-specific versions
    NB: avoid trailing full stops visually, they are added for screen readers in templates
    """
    forms.Field.default_error_messages['required'] = _('This field is required')
    forms.CharField.default_error_messages['min_length'] = _('You’ve entered too few characters')
    forms.CharField.default_error_messages['max_length'] = _('You’ve entered too many characters')
    forms.IntegerField.default_error_messages['invalid'] = _('Enter a whole number')
    forms.FloatField.default_error_messages['invalid'] = _('Enter a number')
    forms.DecimalField.default_error_messages['invalid'] = _('Enter a number')
    forms.DateField.default_error_messages['invalid'] = _('Enter a valid date')
    forms.TimeField.default_error_messages['invalid'] = _('Enter a valid time')
    forms.DateTimeField.default_error_messages['invalid'] = _('Enter a valid date and time')
    forms.FileField.default_error_messages.update({
        'invalid': _('No file was submitted'),
        'missing': _('No file was submitted'),
        'empty': _('The submitted file is empty'),
    })
    forms.SplitDateTimeField.default_error_messages['invalid_date'] = _('Enter a valid date')
    forms.SplitDateTimeField.default_error_messages['invalid_time'] = _('Enter a valid time')
    validators.EmailValidator.message = _('Enter a valid email address')
