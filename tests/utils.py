from unittest import mock

from django.core.urlresolvers import reverse
from django.template import Origin, Template, TemplateDoesNotExist
from django.template.loaders.app_directories import Loader
from django.test import SimpleTestCase as DjangoSimpleTestCase


def get_template_source():
    # mock this function in tests
    return 'dummy'


class DummyTemplateLoader(Loader):
    is_usable = True

    def get_template(self, template_name, template_dirs=None, skip=None):
        try:
            return super(DummyTemplateLoader, self).get_template(
                template_name,
                template_dirs=template_dirs,
                skip=skip
            )
        except TemplateDoesNotExist:
            template_source = get_template_source()
            origin = Origin(template_name, template_name)
            return Template(template_source, origin, template_name, self.engine)


class SimpleTestCase(DjangoSimpleTestCase):
    @mock.patch('tests.urls.get_context')
    @mock.patch('tests.utils.get_template_source')
    def load_mocked_template(self, template, context, mocked_template, mocked_context):
        mocked_template.return_value = template
        mocked_context.return_value = context
        return self.client.get(reverse('dummy'))
