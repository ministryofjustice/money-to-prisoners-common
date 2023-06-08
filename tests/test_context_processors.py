from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now

now_text = now().isoformat()


class ContextProcessorTestCase(SimpleTestCase):
    @override_settings(APP=None, ENVIRONMENT=None)
    def test_context_processors_with_empty_settings(self):
        response = self.client.get(reverse('dummy'))
        self.assertIsNone(response.context.get('GA4_MEASUREMENT_ID'))
        self.assertFalse(response.context.get('analytics_policy').ga4_enabled)
        self.assertIsNone(response.context.get('analytics_policy').ga4_measurement_id)
        self.assertIsNone(response.context.get('APP'))
        self.assertIsNone(response.context.get('ENVIRONMENT'))

    @override_settings(GA4_MEASUREMENT_ID='G-ABCDEF00AB',
                       APP='sample', ENVIRONMENT='dev',
                       APP_GIT_COMMIT='9e50f6ce3b9f5d373d726c9339bf2296d75d4eb2',
                       APP_BUILD_DATE=now_text)
    def test_context_processors_with_settings(self):
        response = self.client.get(reverse('dummy'))
        self.assertTrue(response.context.get('analytics_policy').ga4_enabled)
        self.assertEqual(response.context.get('analytics_policy').ga4_measurement_id, 'G-ABCDEF00AB')
        self.assertEqual(response.context.get('APP'), 'sample')
        self.assertEqual(response.context.get('ENVIRONMENT'), 'dev')
        self.assertEqual(response.context.get('APP_GIT_COMMIT'), '9e50f6ce3b9f5d373d726c9339bf2296d75d4eb2')
        self.assertEqual(response.context.get('APP_BUILD_DATE'), now_text)
