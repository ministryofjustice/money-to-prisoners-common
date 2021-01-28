import os
import re
import subprocess
import sys
import unittest

from mtp_common.build_tasks.app import App
from mtp_common.test_utils.code_style import CodeStyleTestCase  # noqa


class CommonCodeStyleTestCase(unittest.TestCase):
    root_path = os.path.dirname(os.path.dirname(__file__))
    tools = ('eslint', 'sass-lint')
    node_bin_path = './node_modules/.bin'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.install_tools()
        cls.app = App('common', root_path=cls.root_path)

    @classmethod
    def get_tool_bin(cls, tool):
        return os.path.join(cls.node_bin_path, tool)

    @classmethod
    def install_tools(cls):
        if all(os.path.exists(cls.get_tool_bin(tool)) for tool in cls.tools):
            return
        sys.stdout.flush()
        subprocess.check_call(['npm', 'install'], cwd=cls.root_path, env=os.environ)
        sys.stdout.flush()

    def fail_with_output(self, output):
        re_file_path = re.compile(r'^%s' % re.escape(self.root_path))
        self.fail('Code style checks failed\n\n%s' % '\n'.join(
            re_file_path.sub('.', line, count=1)
            for line in output.splitlines()
        ))

    def run_node_tool(self, tool, *args):
        error = None
        try:
            subprocess.run(
                [self.get_tool_bin(tool)] + list(args),
                cwd=self.root_path,
                env=os.environ,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            error = e
        if error:
            self.fail_with_output(error.stdout.decode() + '\n' + error.stderr.decode())

    def get_config_file(self, file_name):
        return os.path.join(self.app.templates_path, 'mtp_common', 'build_tasks', file_name)

    def test_javascript_code_style(self):
        self.run_node_tool(
            'eslint',
            '--config', self.get_config_file('eslintrc.json'),
            '--format', 'stylish',
            self.app.javascript_source_path,
        )

    def test_stylesheets_code_style(self):
        self.run_node_tool(
            'sass-lint',
            '--verbose',
            '--config', self.get_config_file('sass-lint.yml'),
            '--format', 'stylish',
            '--syntax', 'scss',
            os.path.join(self.app.scss_source_path, '**', '*.scss'),
        )
