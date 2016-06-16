#!/usr/bin/env python
import argparse
import os
import sys

import django
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.test.runner import DiscoverRunner

DEFAULT_SETTINGS = dict(
    DEBUG=True,
    SECRET_KEY='a' * 24,
    ROOT_URLCONF='tests.urls',
    INSTALLED_APPS=(
        'mtp_common',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.auth',
        'django.contrib.messages',
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
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'mtp_common.context_processors.analytics',
                'mtp_common.context_processors.app_environment',
                'django.contrib.messages.context_processors.messages'
            ],
            'loaders': ['tests.utils.DummyTemplateLoader']
        },
    }],
    MIDDLEWARE_CLASSES=(
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'mtp_common.auth.csrf.CsrfViewMiddleware',
        'mtp_common.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ),
    CSRF_FAILURE_VIEW='mtp_common.auth.csrf.csrf_failure',
    LOGIN_URL=reverse_lazy('login'),
    LOGOUT_URL=reverse_lazy('logout'),
    LOGIN_REDIRECT_URL=reverse_lazy('dummy'),
)


def run_tests():
    if 'setup.py' in sys.argv:
        # allows `python setup.py test` as well as `python tests`
        sys.argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('test_labels', nargs='*', default=['tests'])
    parser.add_argument('--verbosity', type=int, choices=list(range(4)), default=1)
    parser.add_argument('--noinput', dest='interactive',
                        action='store_false', default=True)
    args = parser.parse_args()

    if not settings.configured:
        settings.configure(**DEFAULT_SETTINGS)
    django.setup()

    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)

    failures = DiscoverRunner(verbosity=args.verbosity, interactive=args.interactive,
                              failfast=False).run_tests(args.test_labels)
    sys.exit(failures)


if __name__ == '__main__':
    run_tests()
