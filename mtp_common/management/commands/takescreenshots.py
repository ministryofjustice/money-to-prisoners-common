import os

from django.core.management.commands.test import Command as TestCommand


class Command(TestCommand):

    def handle(self, *test_labels, **options):
        options['pattern'] = 'test_screenshots.py'
        os.environ['GENERATE_SCREENSHOTS'] = 'True'
        super(Command, self).handle(*test_labels, **options)
        del os.environ['GENERATE_SCREENSHOTS']
