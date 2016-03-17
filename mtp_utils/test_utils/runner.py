import logging

from django.test.runner import DiscoverRunner


class TestRunner(DiscoverRunner):
    """
    A simple extension to the default test runner which silences non-error
    MTP log messages in non-verbose mode as they make the tests difficult to read
    """

    def run_suite(self, suite, **kwargs):
        if self.verbosity < 2:
            logger = logging.getLogger('mtp')
            logger.setLevel(logging.ERROR)
        return super(TestRunner, self).run_suite(suite, **kwargs)
