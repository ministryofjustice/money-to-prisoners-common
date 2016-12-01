from distutils.core import Command, DistutilsArgError
import distutils.log
import os
import re

from setuptools.command.sdist import sdist
try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None


class SetVersion(Command):
    description = 'Set version of MTP common'
    user_options = [('version=', None, 'new version')]

    def initialize_options(self):
        self.version = None

    def finalize_options(self):
        try:
            self.version = list(map(int, self.version.split('.')))
            assert len(self.version) == 3
        except (AttributeError, ValueError, AssertionError):
            raise DistutilsArgError('Version must be in the form N.N.N')

    def run(self):
        replacements = [
            (r'^VERSION =.*$',
             'VERSION = (%s)' % ', '.join(map(str, self.version)),
             'mtp_common/__init__.py'),
            (r'^  "version":.*$',
             '  "version": "%s",' % '.'.join(map(str, self.version)),
             'package.json'),
        ]
        for search, replacement, path in replacements:
            with open(os.path.join(os.path.dirname(__file__), path)) as f:
                content = f.read()
            content = re.sub(search, replacement, content, flags=re.MULTILINE)
            with open(os.path.join(os.path.dirname(__file__), path), 'w') as f:
                f.write(content)


def wrap_run(command_class):
    old_run = command_class.run

    def run(self):
        from django.core.management import call_command

        cwd = os.getcwd()
        os.chdir(os.path.join(os.path.dirname(__file__), 'mtp_common'))
        self.announce('Compiling messages', level=distutils.log.INFO)
        call_command('compilemessages')
        os.chdir(cwd)

        old_run(self)

    command_class.run = run
    command_class.description = '%s; with .mo compilation' % command_class.description
    return command_class


command_classes = {
    'set_version': SetVersion,
    'sdist': wrap_run(sdist),
}
if bdist_wheel:
    command_classes['bdist_wheel'] = wrap_run(bdist_wheel)
