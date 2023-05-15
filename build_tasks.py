import glob
import os
import re
import sys
from unittest import mock

from mtp_common.build_tasks.executor import Context, Tasks, TaskError
from mtp_common.build_tasks import tasks as shared_tasks
from mtp_common.build_tasks.paths import paths_for_shell

tasks = shared_tasks.tasks = Tasks()  # unregister all existing tasks
tasks.register(hidden=True)(shared_tasks.create_build_paths.func)
tasks.register('python_dependencies', 'setup_django_for_testing', hidden=True)(shared_tasks.compile_messages.func)
tasks.register('python_dependencies', 'setup_django_for_testing')(shared_tasks.make_messages.func)
tasks.register(hidden=True)(shared_tasks.precompile_python_code.func)
tasks.register('python_dependencies')(shared_tasks.translations.func)
tasks.register(hidden=True)(shared_tasks.lint_config.func)

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
        APP_GIT_COMMIT='0000000',
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
        LANGUAGE_CODE='en-gb',
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
                    'mtp_common.context_processors.govuk_localisation',
                ],
            },
        }],
        MIDDLEWARE=(
            'mtp_common.metrics.middleware.RequestMetricsMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.CommonMiddleware',
            'mtp_common.auth.csrf.CsrfViewMiddleware',
            'mtp_common.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'django.middleware.security.SecurityMiddleware',
        ),
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            },
        },
        CSRF_FAILURE_VIEW='mtp_common.auth.csrf.csrf_failure',
        LOGIN_URL=reverse_lazy('login'),
        LOGOUT_URL=reverse_lazy('logout'),
        LOGIN_REDIRECT_URL=reverse_lazy('dummy'),

        HMPPS_CLIENT_ID='mtp',
        HMPPS_CLIENT_SECRET='mtp-secret',
        HMPPS_AUTH_BASE_URL='https://noms-auth-dev.local',
        HMPPS_PRISON_API_BASE_URL='https://noms-api-dev.local',
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


@tasks.register('python_dependencies', 'compile_messages', 'precompile_python_code', default=True)
def build(_: Context):
    """
    Builds all necessary assets
    """


@tasks.register('setup_django_for_testing', 'lint_config', 'build')
def test(context: Context, test_labels=None):
    """
    Tests the app
    """
    from django.test.runner import DiscoverRunner

    python_dependencies(context, extras='testing')
    test_labels = (test_labels or 'tests').split()
    return DiscoverRunner(verbosity=context.verbosity, interactive=False, failfast=False).run_tests(test_labels)


@tasks.register()
def bump_version(context: Context, major=False, minor=False, patch=False):
    """
    Bumps the version of MTP-common, commits and tags the change
    """
    bump_levels = [major, minor, patch]
    if bump_levels.count(True) != 1:
        raise TaskError('Specify either --major, --minor or --patch')

    from mtp_common import VERSION

    version = list(VERSION)
    level = bump_levels.index(True)
    version[level] += 1  # bump selected level
    version[level + 1:] = [0] * (len(version) - 1 - level)  # set lower levels to 0

    # true if there are uncommitted changes before version is bumped
    git_already_dirty = any(map(bool, (
        context.shell('git', 'diff', '--quiet'),
        context.shell('git', 'diff', '--quiet', '--cached')
    )))

    dotted_version = '.'.join(map(str, version))
    replacements = [
        (r'^VERSION =.*$',
         'VERSION = (%s)' % ', '.join(map(str, version)),
         'mtp_common/__init__.py'),
        (r'^  "version":.*$',
         f'  "version": "{dotted_version}",',
         'package.json'),
    ]
    for search, replacement, path in replacements:
        with open(os.path.join(root_path, path)) as f:
            content = f.read()
        content = re.sub(search, replacement, content, flags=re.MULTILINE)
        with open(os.path.join(root_path, path), 'w') as f:
            f.write(content)
    context.info(f'Updated version to {dotted_version}')

    if git_already_dirty:
        context.error('Cannot commit version bump because repository was already dirty')
        return

    context.shell('git', 'checkout', 'main')
    context.shell('git', 'add', *[path for _, _, path in replacements])
    context.shell('git', 'commit', '--message', f'"Bump to {dotted_version}"')
    context.shell('git', 'tag', dotted_version)
    context.shell('git', 'push', '--atomic', 'origin', 'main', dotted_version)
    context.info('Publish to PyPI by creating new release:\n'
                 'https://github.com/ministryofjustice/money-to-prisoners-common/releases/new?'
                 f'tag={dotted_version}&'
                 f'title={dotted_version}')


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
    context.shell(sys.executable, 'setup.py', 'sdist', 'bdist_wheel')
    context.shell('twine', 'upload', '--non-interactive', 'dist/*')


@tasks.register()
def clean(context: Context, delete_dependencies: bool = False):
    """
    Deletes build outputs
    """
    paths = ['docs/build', 'build', 'dist', '.eggs'] + glob.glob('*.egg-info')
    context.shell('rm -rf %s' % paths_for_shell(paths))
    context.shell(f'find {context.app.django_app_name} -name "*.pyc" -delete')
    context.shell(f'find {context.app.django_app_name} -name __pycache__ -delete')

    if delete_dependencies:
        context.info('Cleaning local %s dependencies' % context.app.name)
        paths = ['venv']
        context.shell('rm -rf %s' % paths_for_shell(paths))
