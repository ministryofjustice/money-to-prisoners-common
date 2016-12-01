import os
import subprocess
import sys

from mtp_common.build_tasks.app import App
from mtp_common.test_utils.code_style import CodeStyleTestCase


class CommonCodeStyleTestCase(CodeStyleTestCase):
    root_path = os.path.dirname(os.path.dirname(__file__))

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.stdout.flush()
        subprocess.check_call(['npm', 'install'], cwd=cls.root_path)
        cls.app = App('common', root_path=cls.root_path)

    def run_node_tool(self, tool, *args):
        try:
            subprocess.check_output(['./node_modules/.bin/' + tool] + list(args), cwd=self.root_path)
        except subprocess.CalledProcessError as e:
            self.fail('Code style checks failed\n\n%s' % e.output.decode('utf-8'))

    def get_config_file(self, file_name):
        return os.path.join(self.app.common_templates_path, 'mtp_common', 'build_tasks', file_name)

    def test_javascript_code_style(self):
        self.run_node_tool('eslint',
                           '--config', self.get_config_file('eslintrc.json'),
                           '--format', 'stylish',
                           self.app.javascript_source_path)

    def test_stylesheets_code_style(self):
        self.run_node_tool('sass-lint',
                           '--config', self.get_config_file('sass-lint.yml'),
                           '--format', 'stylish',
                           '--syntax', 'scss',
                           os.path.join(self.app.scss_source_path, '**', '*.scss'))
