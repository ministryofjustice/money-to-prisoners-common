from unittest import mock

from django.test import SimpleTestCase as DjangoSimpleTestCase
from django.urls import reverse


class SimpleTestCase(DjangoSimpleTestCase):
    @mock.patch('tests.urls.mocked_context')
    @mock.patch('tests.urls.mocked_template')
    def load_mocked_template(self, template, context, mocked_template, mocked_context):
        mocked_template.return_value = template
        mocked_context.return_value = context
        return self.client.get(reverse('dummy'))
