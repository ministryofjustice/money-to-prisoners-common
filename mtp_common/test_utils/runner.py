import logging
import os

from django.conf import settings
from django.test.runner import DiscoverRunner


class TestRunner(DiscoverRunner):
    """
    A simple extension to the default test runner which silences non-error
    MTP log messages in non-verbose mode as they make the tests difficult to read.
    Also wraps test suite with accessibility testing if requested.
    """

    def run_suite(self, suite, **kwargs):
        if 'RUN_ACCESSIBILITY_TESTS' in os.environ:
            from mtp_common.test_utils.functional_tests import enable_accessibility

            middleware = 'mtp_common.test_utils.functional_tests.AccessibilityTestingMiddleware'
            if middleware not in settings.MIDDLEWARE:
                settings.MIDDLEWARE += (middleware,)
            enable_accessibility(suite)

        if self.verbosity < 2:
            logging.getLogger().setLevel(logging.ERROR)
            logging.getLogger('mtp').setLevel(logging.ERROR)

        return super().run_suite(suite, **kwargs)
