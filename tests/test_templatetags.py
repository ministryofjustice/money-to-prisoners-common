import decimal
from unittest import mock

from django import forms

from tests.utils import SimpleTestCase


class TemplateTagTestCase(SimpleTestCase):
    def test_to_string_filter(self):
        class MagicInt(int):
            def __str__(self):
                return 'magic'

        template = """
        {% load mtp_common %}
        {% if magic_int in ints %}PASS1{% endif %}
        {% if magic_int|to_string in ints %}FAIL1{% endif %}
        {% if magic_int in strs %}FAIL2{% endif %}
        {% if magic_int|to_string in strs %}PASS2{% endif %}
        """
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

        template = """
        {% load mtp_common %}
        {% with field=form|field_from_name:'missing_field' %}
            -{{ field.value }}-
        {% endwith %}
        {% with field=form|field_from_name:'test_field' %}
            +{{ field.value }}+
        {% endwith %}
        """
        response = self.load_mocked_template(template, {
            'form': TestForm(data={
                'test_field': 123
            }),
        })
        html = response.content.decode('utf-8')
        self.assertIn('--', html)
        self.assertIn('+123+', html)

    def test_choices_with_help_text(self):
        def render(help_texts):
            class TestForm(forms.Form):
                option = forms.ChoiceField(choices=[('a', 'A'), ('b', 'B')])
                option_choices_help_text = help_texts

            template = """
            {% load mtp_common %}
            {% choices_with_help_text form.option.field.choices form.option_choices_help_text as choices %}
            """
            response = self.load_mocked_template(template, {
                'form': TestForm(),
            })
            return response.context['choices']

        # usual case where there are equal numbers of choices and help texts
        choices_with_help_text = render(['first', 'second'])
        self.assertSequenceEqual(
            choices_with_help_text,
            [('a', 'A', 'first'), ('b', 'B', 'second')],
        )

        # no help texts
        choices_with_help_text = render(None)
        self.assertSequenceEqual(
            choices_with_help_text,
            [('a', 'A', ''), ('b', 'B', '')],
        )

        # length mismatch
        choices_with_help_text = render(['first'])
        self.assertSequenceEqual(
            choices_with_help_text,
            [('a', 'A', 'first'), ('b', 'B', '')],
        )

    @mock.patch('mtp_common.templatetags.mtp_common.sentry_client')
    def test_sentry_tag(self, mocked_sentry_client):
        sentry_dsn = 'http://sentry.example.com/123'
        mocked_sentry_client.get_options.return_value.get.return_value = sentry_dsn

        template = """
        {% load mtp_common %}
        {% sentry_js %}
        """
        response = self.load_mocked_template(template, {})
        html = response.content.decode('utf-8')
        self.assertIn(sentry_dsn, html)
        self.assertIn('Sentry.init', html)

    def test_page_list(self):
        template = """
        {% load mtp_common %}
        {% page_list page=current_page page_count=pages query_string=query_string %}
        """

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
        self.assertNotIn('?page=2', render(2, 2))

        self.assertIn('?a=b&amp;page=2', render(1, 2, 'a=b'))

        many_pages = render(7, 100)
        self.assertIn('…', many_pages)
        expected_pages = (1, 6, 8, 100)
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

    def test_format_currency(self):
        def render(template, value, expected):
            template = '{% load mtp_common %}' + template
            response = self.load_mocked_template(template, {'value': value})
            content = response.content.decode('utf-8')
            self.assertEqual(expected, content)

        template = '{{ value|currency }}'
        render(template, 0, '£0.00')
        render(template, 1, '£0.01')
        render(template, 100, '£1.00')
        render(template, -4210, '-£42.10')
        render(template, 30000, '£300.00')
        render(template, 1841691287201, '£18,416,912,872.01')
        render(template, decimal.Decimal('1234567890'), '£12,345,678.90')
        for invalid in (False, True, None, '', '1234'):
            render(template, invalid, str(invalid))

        template = '{% currency value %}'
        render(template, 0, '£0.00')
        render(template, 1, '£0.01')
        render(template, 100, '£1.00')
        render(template, -4210, '-£42.10')
        render(template, 30000, '£300.00')
        render(template, 1841691287202, '£18,416,912,872.02')
        render(template, decimal.Decimal('1234567890'), '£12,345,678.90')
        for invalid in (False, True, None, '', '1234'):
            render(template, invalid, str(invalid))

        template = "{% currency value '' %}"
        render(template, 0, '0.00')
        render(template, 1, '0.01')
        render(template, 100, '1.00')
        render(template, -4210, '-42.10')
        render(template, 30000, '300.00')
        render(template, 1841691287203, '18,416,912,872.03')
        render(template, decimal.Decimal('1234567890'), '12,345,678.90')
        for invalid in (False, True, None, '', '1234'):
            render(template, invalid, str(invalid))

        template = '{% currency value trim_empty_pence=True %}'
        render(template, 0, '£0')
        render(template, 1, '£0.01')
        render(template, 100, '£1')
        render(template, -4200, '-£42')
        render(template, 30000, '£300')
        render(template, 1841691287200, '£18,416,912,872')
        render(template, decimal.Decimal('1234567800'), '£12,345,678')
        for invalid in (False, True, None, '', '1234'):
            render(template, invalid, str(invalid))

    def test_format_postcode(self):
        def render(postcode, expected):
            template = '{% load mtp_common %}{{ postcode|postcode }}'
            response = self.load_mocked_template(template, {'postcode': postcode})
            content = response.content.decode('utf-8')
            self.assertEqual(expected, content)

        render('SW1H9AJ', 'SW1H 9AJ')
        render('sw1h9aj', 'SW1H 9AJ')
        render('sw1h 9aj', 'SW1H 9AJ')
        render('BS78PS', 'BS7 8PS')
        render('M609AH', 'M60 9AH')
        render('ME173DF', 'ME17 3DF')
        render('abc123', 'ABC123')
        render('75008', '75008')
        render(75008, '75008')

    def test_counter(self):
        response = self.load_mocked_template("""
            {% load mtp_common %}
            {% create_counter 'test' %}
            {% increment_counter 'test' %}
        """, {})
        html = response.content.decode().strip()
        self.assertEqual(html, '1')

        response = self.load_mocked_template("""
            {% load mtp_common %}
            {% create_counter 'test' %}
            {% increment_counter 'test' %},{% increment_counter 'test' %},{% increment_counter 'test' %}
        """, {})
        html = response.content.decode().strip()
        self.assertEqual(html, '1,2,3')

        response = self.load_mocked_template("""
            {% load mtp_common %}
            {% create_counter a %}
            {% create_counter b %}
            {% increment_counter a %},{% increment_counter a %},{% increment_counter b %},{% increment_counter a %}
        """, {'a': 'test1', 'b': 'test2'})
        html = response.content.decode().strip()
        self.assertEqual(html, '1,2,1,3')
