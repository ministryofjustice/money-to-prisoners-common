from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now

now_text = now().isoformat()


class ContextProcessorTestCase(SimpleTestCase):
    @override_settings(APP=None, ENVIRONMENT=None)
    def test_context_processors_with_empty_settings(self):
        response = self.client.get(reverse('dummy'))
        self.assertIsNone(response.context.get('GOOGLE_ANALYTICS_ID'))
        self.assertFalse(response.context.get('analytics_policy').enabled)
        self.assertIsNone(response.context.get('analytics_policy').google_analytics_id)
        self.assertIsNone(response.context.get('APP'))
        self.assertIsNone(response.context.get('ENVIRONMENT'))

    @override_settings(GOOGLE_ANALYTICS_ID='UA-11223344-00',
                       APP='sample', ENVIRONMENT='dev',
                       APP_GIT_COMMIT='9e50f6ce3b9f5d373d726c9339bf2296d75d4eb2',
                       APP_BUILD_DATE=now_text)
    def test_context_processors_with_settings(self):
        response = self.client.get(reverse('dummy'))
        self.assertEqual(response.context.get('analytics_policy').google_analytics_id, 'UA-11223344-00')
        self.assertEqual(response.context.get('APP'), 'sample')
        self.assertEqual(response.context.get('ENVIRONMENT'), 'dev')
        self.assertEqual(response.context.get('APP_GIT_COMMIT'), '9e50f6ce3b9f5d373d726c9339bf2296d75d4eb2')
        self.assertEqual(response.context.get('APP_BUILD_DATE'), now_text)
