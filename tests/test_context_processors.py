from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from django.test.utils import override_settings


class ContextProcessorTestCase(SimpleTestCase):
    def test_context_processors_with_empty_settings(self):
        response = self.client.get(reverse('dummy'))
        self.assertEqual(response.context.get('GOOGLE_ANALYTICS_ID'),
                         None)
        self.assertEqual(response.context.get('APP'), None)
        self.assertEqual(response.context.get('ENVIRONMENT'), None)

    @override_settings(GOOGLE_ANALYTICS_ID='UA-11223344-00',
                       APP='sample', ENVIRONMENT='dev')
    def test_context_processors_with_settings(self):
        response = self.client.get(reverse('dummy'))
        self.assertEqual(response.context.get('GOOGLE_ANALYTICS_ID'),
                         'UA-11223344-00')
        self.assertEqual(response.context.get('APP'), 'sample')
        self.assertEqual(response.context.get('ENVIRONMENT'), 'dev')
