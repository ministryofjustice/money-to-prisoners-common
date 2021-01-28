from django import forms

from tests.utils import SimpleTestCase


class TestForm(forms.Form):
    test_field = forms.CharField(label='FIELD A', required=True)
    create_general_error = False

    def clean(self):
        if self.create_general_error:
            self.add_error(None, 'General error')
        return super().clean()


template = """
{% include 'govuk-frontend/components/error-summary.html' with form=form only %}
"""


class ErrorSummaryTestCase(SimpleTestCase):
    def test_no_summary_if_no_errors(self):
        form = TestForm(data={'test_field': 'test'})
        response = self.load_mocked_template(template, {'form': form})
        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode(response.charset)
        self.assertNotIn('There was a problem', response_content)
        self.assertNotIn('General error', response_content)
        self.assertNotIn('FIELD A', response_content)
        self.assertNotIn('error-summary', response_content)

    def test_field_summary_shows(self):
        form = TestForm(data={})
        response = self.load_mocked_template(template, {'form': form})
        self.assertContains(response, 'There was a problem')
        response_content = response.content.decode(response.charset)
        self.assertNotIn('General error', response_content)
        self.assertIn('FIELD A', response_content)

    def test_non_field_summary_shows(self):
        form = TestForm(data={'test_field': 'test'})
        form.create_general_error = True
        response = self.load_mocked_template(template, {'form': form})
        self.assertContains(response, 'There was a problem')
        response_content = response.content.decode(response.charset)
        self.assertIn('General error', response_content)
        self.assertNotIn('FIELD A', response_content)

    def test_complete_summary_shows(self):
        form = TestForm(data={})
        form.error_summary_title = 'The form has errors'
        form.create_general_error = True
        response = self.load_mocked_template(template, {'form': form})
        self.assertContains(response, 'The form has errors')
        response_content = response.content.decode(response.charset)
        self.assertIn('General error', response_content)
        self.assertIn('FIELD A', response_content)
