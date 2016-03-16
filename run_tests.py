#!/usr/bin/env python
import argparse
import os
import sys

import django
from django.conf import settings
from django.test.runner import DiscoverRunner

DEFAULT_SETTINGS = dict(
    DEBUG=True,
    SECRET_KEY='a' * 24,
    ROOT_URLCONF='tests.urls',
    INSTALLED_APPS=(
        'mtp_utils',
    ),
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'mtp_utils.context_processors.analytics',
                'mtp_utils.context_processors.app_environment',
            ],
            'loaders': ['tests.utils.DummyTemplateLoader']
        },
    }],
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

    # root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # if root_path not in sys.path:
    #     sys.path.insert(0, root_path)

    django.setup()

    failures = DiscoverRunner(verbosity=args.verbosity, interactive=args.interactive,
                              failfast=False).run_tests(args.test_labels)
    sys.exit(failures)


if __name__ == '__main__':
    run_tests()
