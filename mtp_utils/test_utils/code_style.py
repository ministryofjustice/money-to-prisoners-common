import io
import os
import re
import sys
import unittest

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from flake8.engine import get_style_guide


class CodeStyleTestCase(unittest.TestCase):
    @classmethod
    def get_root_path(cls):
        if hasattr(cls, 'root_path'):
            return cls.root_path
        try:
            root_path = os.path.join(settings.BASE_DIR, os.path.pardir)
            return os.path.abspath(root_path)
        except (ImproperlyConfigured, AttributeError):
            root_path = os.path.dirname(__file__)
            for _ in range(10):
                root_path = os.path.join(root_path, os.path.pardir)
                if os.path.isfile(os.path.join(root_path, 'setup.cfg')):
                    return os.path.abspath(root_path)
        raise FileNotFoundError('Cannot find setup.cfg')

    def test_app_python_code_style(self):
        root_path = self.get_root_path()
        flake8_style = get_style_guide(
            config_file=os.path.join(root_path, 'setup.cfg'),
            paths=[root_path],
        )
        stdout, sys.stdout = sys.stdout, io.StringIO()
        report = flake8_style.check_files()
        output, sys.stdout = sys.stdout, stdout
        if report.total_errors:
            message = '\n\n'
            line_prefix = re.compile(r'^%s' % root_path)
            output.seek(0)
            for line in output.readlines():
                line = line_prefix.sub('', line).lstrip('/')
                message += line
            self.fail(message)
