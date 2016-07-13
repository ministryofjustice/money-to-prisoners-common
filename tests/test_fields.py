import datetime
from unittest import mock

from django import forms
from django.test import SimpleTestCase
from django.utils.timezone import utc

from mtp_common.forms.fields import SplitDateField, YearField


class DateFieldTestCase(SimpleTestCase):
    class TestForm(forms.Form):
        dob = SplitDateField()

    def test_successful_date_entry(self):
        form = self.TestForm(data={
            'dob_0': '2',
            'dob_1': '5',
            'dob_2': '1982',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['dob'], datetime.date(1982, 5, 2))

    def test_successful_short_year_date_entry(self):
        form = self.TestForm(data={
            'dob_0': '2',
            'dob_1': '5',
            'dob_2': '82',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['dob'], datetime.date(1982, 5, 2))

    def test_recent_short_year_date_entry(self):
        year = datetime.date.today().year
        entry_year = int(str(year)[-2:]) - 11
        form = self.TestForm(data={
            'dob_0': '2',
            'dob_1': '5',
            'dob_2': str(entry_year),
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['dob'], datetime.date(year - 11, 5, 2))

    def test_distant_short_year_date_entry(self):
        year = datetime.date.today().year
        entry_year = int(str(year)[-2:]) - 31
        form = self.TestForm(data={
            'dob_0': '2',
            'dob_1': '5',
            'dob_2': str(entry_year),
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['dob'], datetime.date(year - 31, 5, 2))

    def test_missing_date_entry(self):
        form = self.TestForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required', form.errors.as_text())

    def test_invalid_date_entry(self):
        form = self.TestForm(data={
            'dob_0': '31',
            'dob_1': '2',
            'dob_2': '1982',
        })
        self.assertFalse(form.is_valid())
        self.assertIn(SplitDateField.default_error_messages['invalid'], form.errors.as_text())

    def test_invalid_number_entry(self):
        form = self.TestForm(data={
            'dob_0': '',
            'dob_1': '2',
            'dob_2': '1982',
        })
        self.assertFalse(form.is_valid())

    @mock.patch('mtp_common.forms.fields.now', return_value=datetime.datetime(2016, 7, 13, tzinfo=utc))
    def test_2_digit_year_entry(self, _):
        field = YearField()
        for year in range(100):
            if year <= 6:
                self.assertEqual(field.clean(year), year + 2000)
            else:
                self.assertEqual(field.clean(year), year + 1900)

    @mock.patch('mtp_common.forms.fields.now', return_value=datetime.datetime(2181, 1, 1, tzinfo=utc))
    def test_2_digit_year_entry_next_century(self, _):
        era_boundary = 70  # make it 11 years prior as opposed to 10
        field = YearField(era_boundary=era_boundary)
        for year in range(100):
            if year <= era_boundary:
                self.assertEqual(field.clean(year), year + 2100)
            else:
                self.assertEqual(field.clean(year), year + 2000)
