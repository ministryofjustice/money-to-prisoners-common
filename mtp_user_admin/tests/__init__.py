from django.template import Origin, Template, TemplateDoesNotExist
from django.template.loaders.app_directories import Loader


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
