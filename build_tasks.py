import glob
import os
import re
import sys
from unittest import mock

from mtp_common.build_tasks.executor import Context, Tasks, TaskError
from mtp_common.build_tasks import tasks as shared_tasks
from mtp_common.build_tasks.paths import paths_for_shell

tasks = shared_tasks.tasks = Tasks()  # unregister all existing tasks
tasks.register('create_build_paths')(shared_tasks.govuk_template.func)
tasks.register(hidden=True)(shared_tasks.create_build_paths.func)
tasks.register('python_dependencies', 'setup_django_for_testing', hidden=True)(shared_tasks.compile_messages.func)
tasks.register('python_dependencies', 'setup_django_for_testing')(shared_tasks.make_messages.func)
tasks.register(hidden=True)(shared_tasks.precompile_python_code.func)
tasks.register('python_dependencies')(shared_tasks.translations.func)

root_path = os.path.abspath(os.path.dirname(__file__))


@tasks.register('python_dependencies', hidden=True)
def setup_django_for_testing(_: Context):
    """
    Setup django settings for testing
    """
    import django
    from django.conf import settings
    from django.urls import reverse_lazy

    if settings.configured:
        raise TaskError('This task must be called first')
    settings.configure(
        APP='common',
        ENVIRONMENT='test',
        DEBUG=True,
        SECRET_KEY='a' * 24,
        ROOT_URLCONF='tests.urls',
        INSTALLED_APPS=(
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'widget_tweaks',
            'mtp_common',
            'mtp_common.metrics',
        ),
        LANGUAGES=(
            ('en-gb', 'English'),
            ('cy', 'Cymraeg'),
        ),
        OAUTHLIB_INSECURE_TRANSPORT=True,
        API_URL='http://localhost:8000',
        SITE_URL='http://localhost:8001',
        STATIC_URL='/static/',
        API_CLIENT_ID='test-client-id',
        API_CLIENT_SECRET='test-client-secret',
        AUTHENTICATION_BACKENDS=['mtp_common.auth.backends.MojBackend'],
        SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies',
        MESSAGE_STORAGE='django.contrib.messages.storage.session.SessionStorage',
        DEFAULT_FROM_EMAIL='service@mtp.local',
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(root_path, 'tests', 'templates')],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'mtp_common.context_processors.analytics',
                    'mtp_common.context_processors.app_environment',
                ],
            },
        }],
        MIDDLEWARE=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.CommonMiddleware',
            'mtp_common.auth.csrf.CsrfViewMiddleware',
            'mtp_common.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'django.middleware.security.SecurityMiddleware',
        ),
        CSRF_FAILURE_VIEW='mtp_common.auth.csrf.csrf_failure',
        LOGIN_URL=reverse_lazy('login'),
        LOGOUT_URL=reverse_lazy('logout'),
        LOGIN_REDIRECT_URL=reverse_lazy('dummy'),
        NOMIS_API_BASE_URL='https://noms-api-dev.local/nomisapi/',
        NOMIS_API_CLIENT_TOKEN='hello',
        NOMIS_API_PRIVATE_KEY=(
            '-----BEGIN EC PRIVATE KEY-----\n'
            'MHcCAQEEIOhhs3RXk8dU/YQE3j2s6u97mNxAM9s+13S+cF9YVgluoAoGCCqGSM49\n'
            'AwEHoUQDQgAE6l49nl7NN6k6lJBfGPf4QMeHNuER/o+fLlt8mCR5P7LXBfMG6Uj6\n'
            'TUeoge9H2N/cCafyhCKdFRdQF9lYB2jB+A==\n'
            '-----END EC PRIVATE KEY-----\n'
        ),  # this key is just for tests, doesn't do anything
    )
    django.setup()


@tasks.register(hidden=True)
def python_dependencies(context: Context, extras=None):
    """
    Updates python dependencies
    """
    with mock.patch('setuptools.setup'):
        from setup import install_requires, extras_require

        requirements = install_requires.copy()
        if extras:
            requirements.extend(extras_require[extras])
    return context.pip_command('install', *requirements)


@tasks.register('python_dependencies', 'govuk_template', 'compile_messages', 'precompile_python_code', default=True)
def build(_: Context):
    """
    Builds all necessary assets
    """


@tasks.register('setup_django_for_testing', 'build')
def test(context: Context, test_labels=None):
    """
    Tests the app
    """
    from django.test.runner import DiscoverRunner

    python_dependencies(context, extras='testing')
    test_labels = (test_labels or 'tests').split()
    return DiscoverRunner(verbosity=context.verbosity, interactive=False, failfast=False).run_tests(test_labels)


@tasks.register()
def set_version(context: Context, version=None, bump=False):
    """
    Updates the version of MTP-common
    """
    if bump and version:
        raise TaskError('You cannot bump and set a specific version')
    if bump:
        from mtp_common import VERSION

        version = list(VERSION)
        version[-1] += 1
    else:
        try:
            version = list(map(int, version.split('.')))
            assert len(version) == 3
        except (AttributeError, ValueError, AssertionError):
            raise TaskError('Version must be in the form N.N.N')

    dotted_version = '.'.join(map(str, version))
    replacements = [
        (r'^VERSION =.*$',
         'VERSION = (%s)' % ', '.join(map(str, version)),
         'mtp_common/__init__.py'),
        (r'^  "version":.*$',
         '  "version": "%s",' % dotted_version,
         'package.json'),
    ]
    for search, replacement, path in replacements:
        with open(os.path.join(root_path, path)) as f:
            content = f.read()
        content = re.sub(search, replacement, content, flags=re.MULTILINE)
        with open(os.path.join(root_path, path), 'w') as f:
            f.write(content)
    context.debug('Updated version to %s' % dotted_version)


@tasks.register('setup_django_for_testing', hidden=True)
def docs(context: Context):
    """
    Generates static documentation
    """
    try:
        from sphinx.application import Sphinx
    except ImportError:
        context.pip_command('install', 'Sphinx')
        from sphinx.application import Sphinx

    context.shell('cp', 'README.rst', 'docs/README.rst')
    app = Sphinx('docs', 'docs', 'docs/build', 'docs/build/.doctrees', buildername='html', parallel=True,
                 verbosity=context.verbosity)
    app.build()


@tasks.register('clean', 'build')
def upload(context: Context):
    """
    Builds and uploads MTP-common to pypi
    """
    return context.shell(sys.executable, 'setup.py', 'sdist', 'bdist_wheel', 'upload')


@tasks.register()
def clean(context: Context, delete_dependencies: bool = False):
    """
    Deletes build outputs
    """
    paths = ['docs/build', 'build', 'dist', '.eggs'] + glob.glob('*.egg-info')
    context.shell('rm -rf %s' % paths_for_shell(paths))
    context.shell('find %s -name "*.pyc" -or -name __pycache__ -delete' % context.app.django_app_name)

    if delete_dependencies:
        context.info('Cleaning local %s dependencies' % context.app.name)
        paths = ['venv']
        context.shell('rm -rf %s' % paths_for_shell(paths))
