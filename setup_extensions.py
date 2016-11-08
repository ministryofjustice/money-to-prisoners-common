import distutils.log
import os

from setuptools.command.sdist import sdist
try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None


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


command_classes = {'sdist': wrap_run(sdist)}
if bdist_wheel:
    command_classes['bdist_wheel'] = wrap_run(bdist_wheel)
