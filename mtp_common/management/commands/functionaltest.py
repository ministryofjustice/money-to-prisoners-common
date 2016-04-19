import os

from django.core.management.commands.test import Command as TestCommand


class Command(TestCommand):

    def handle(self, *test_labels, **options):
        options['pattern'] = 'test_functional.py'
        os.environ['RUN_FUNCTIONAL_TESTS'] = 'True'

        if options.get('remote_integration_url') is not None:
            os.environ['DJANGO_TEST_REMOTE_INTEGRATION_URL'] = options['remote_integration_url']
            del options['remote_integration_url']
        super(Command, self).handle(*test_labels, **options)

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--remote-integration-url',
            action='store', dest='remote_integration_url', default=None,
            help='Service URL for remote functional tests.'
        )
