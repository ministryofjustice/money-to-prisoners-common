from unittest import mock

from django import forms

from tests.utils import SimpleTestCase


class TemplateTagTestCase(SimpleTestCase):
    def test_to_string_filter(self):
        class MagicInt(int):
            def __str__(self):
                return 'magic'

        template = '''
        {% load mtp_common %}
        {% if magic_int in ints %}PASS1{% endif %}
        {% if magic_int|to_string in ints %}FAIL1{% endif %}
        {% if magic_int in strs %}FAIL2{% endif %}
        {% if magic_int|to_string in strs %}PASS2{% endif %}
        '''
        response = self.load_mocked_template(template, {
            'magic_int': MagicInt(123),
            'ints': [123],
            'strs': ['magic'],
        })

        html = response.content.decode('utf-8')
        self.assertIn('PASS1', html)
        self.assertIn('PASS2', html)
        self.assertNotIn('FAIL1', html)
        self.assertNotIn('FAIL2', html)

    def test_field_from_name_filter(self):
        class TestForm(forms.Form):
            test_field = forms.CharField()

        template = '''
        {% load mtp_common %}
        {% with field=form|field_from_name:'missing_field' %}
            -{{ field.value }}-
        {% endwith %}
        {% with field=form|field_from_name:'test_field' %}
            +{{ field.value }}+
        {% endwith %}
        '''
        response = self.load_mocked_template(template, {
            'form': TestForm(data={
                'test_field': 123
            }),
        })
        html = response.content.decode('utf-8')
        self.assertIn('--', html)
        self.assertIn('+123+', html)

    @mock.patch('mtp_common.templatetags.mtp_common.sentry_client')
    def test_sentry_tag(self, mocked_sentry_client):
        sentry_dsn = 'http://sentry.example.com/123'
        mocked_sentry_client.get_public_dsn.return_value = sentry_dsn

        template = '''
        {% load mtp_common %}
        {% sentry_js %}
        '''
        response = self.load_mocked_template(template, {})
        html = response.content.decode('utf-8')
        self.assertIn("<script>Raven.config('%s').install()</script>" % sentry_dsn, html)
