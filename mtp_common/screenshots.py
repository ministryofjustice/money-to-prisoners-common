import os
from unittest import skipUnless

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.testcases import LiveServerThread
from mtp_common.test_utils.functional_tests import WebDriverControlMixin
from mtp_common.test_utils.webdrivers import ChromeConf


@skipUnless('GENERATE_SCREENSHOTS' in os.environ, 'screenshot generation is disabled')
class ScreenshotGenerator(StaticLiveServerTestCase, WebDriverControlMixin):
    save_as = 'screenshot'
    thread_class = LiveServerThread

    @classmethod
    def _databases_names(cls, include_mirrors=True):
        # MTP client applications do not have databases
        if len(settings.DATABASES):
            return super()._databases_names(include_mirrors=include_mirrors)
        return []

    @classmethod
    def _create_server_thread(cls, connections_override):
        return cls.server_thread_class(
            cls.host,
            cls.static_handler,
            connections_override=connections_override,
            port=cls.port,
        )

    def setUp(self):
        self.driver = ChromeConf().load_driver(headless=True)

    def tearDown(self):
        screenshot_path = '/'.join([
            settings.STATICFILES_DIRS[0],
            self.get_screenshot_path()
        ])
        self.driver.save_screenshot(screenshot_path)
        self.driver.quit()

    def get_screenshot_path(self):
        return 'images/screenshots/%s.png' % self.save_as
