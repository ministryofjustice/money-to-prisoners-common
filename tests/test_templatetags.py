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
        self.assertIn(sentry_dsn, html)
        self.assertIn('Raven.config', html)

    def test_page_list(self):
        template = '''
        {% load mtp_common %}
        {% page_list page=current_page page_count=pages query_string=query_string %}
        '''

        def render(current_page, pages, query_string=''):
            context = {
                'current_page': current_page,
                'pages': pages,
                'query_string': query_string,
            }
            response = self.load_mocked_template(template, context)
            return response.content.decode('utf-8').strip()

        self.assertNotIn('?page=1', render(1, 1))
        self.assertIn('?page=2', render(1, 2))
        self.assertIn('?page=2', render(2, 2))

        self.assertIn('?a=b&amp;page=2', render(1, 2, 'a=b'))

        many_pages = render(7, 100)
        self.assertIn('…', many_pages)
        expected_pages = (1, 2, 5, 6, 7, 8, 9, 99, 100)
        for page in range(100):
            page += 1
            page_link = 'href="?page=%d"' % page
            if page in expected_pages:
                self.assertIn(page_link, many_pages)
            else:
                self.assertNotIn(page_link, many_pages)

    def test_and_join(self):
        def render(values, expected, unexpected=None):
            template = '{% load mtp_common %}{{ values|and_join }}'
            response = self.load_mocked_template(template, {'values': values})
            content = response.content.decode('utf-8')
            self.assertEqual(expected, content)
            if unexpected:
                self.assertNotIn(unexpected, content)

        render([], '', 'and')
        render(['a'], 'a', 'and')
        render([1], '1', 'and')
        render([1, 'b'], '1 and b')
        render(range(10), '0, 1, 2, 3, 4, 5, 6, 7, 8 and 9')
