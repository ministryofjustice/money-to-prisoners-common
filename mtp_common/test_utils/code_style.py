import os
import subprocess
import unittest

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class CodeStyleTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if hasattr(cls, 'root_path'):
            return
        try:
            root_path = os.path.join(settings.BASE_DIR, os.path.pardir)
            cls.root_path = os.path.abspath(root_path)
            return
        except (ImproperlyConfigured, AttributeError):
            root_path = os.path.dirname(__file__)
            for _ in range(10):
                root_path = os.path.join(root_path, os.path.pardir)
                if os.path.isfile(os.path.join(root_path, 'setup.cfg')):
                    cls.root_path = os.path.abspath(root_path)
                    return
        raise FileNotFoundError('Cannot find setup.cfg')

    def test_app_python_code_style(self):
        try:
            command = './venv/bin/flake8' if os.path.exists(os.path.join(self.root_path, 'venv')) else 'flake8'
            subprocess.check_output([command], cwd=self.root_path, env=os.environ)
        except subprocess.CalledProcessError as e:
            self.fail('Code style checks failed\n\n%s' % e.output.decode('utf-8'))
