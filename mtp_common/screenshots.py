import os
from unittest import skipUnless

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.testcases import LiveServerThread
from mtp_common.test_utils.functional_tests import WebDriverControlMixin
from selenium import webdriver


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
    def _create_server_thread(cls, host, possible_ports, connections_override):
        return cls.thread_class(
            host,
            possible_ports,
            cls.static_handler,
            connections_override=connections_override,
        )

    def setUp(self):
        path = './node_modules/phantomjs-prebuilt/lib/phantom/bin/phantomjs'
        self.driver = webdriver.PhantomJS(executable_path=path)
        self.driver.command_executor._commands['executePhantom'] = (
            'POST', '/session/$sessionId/phantom/execute'
        )
        self.execute_phantom('this.zoomFactor = 2;')
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1900, 2000)
        self.set_screenshot_size()

    def execute_phantom(self, script):
        self.driver.execute('executePhantom', {'script': script, 'args': []})

    def set_screenshot_size(self, top=0, left=0, width=1860, height=1240):
        self.execute_phantom(
            'this.clipRect = {top:%(top)s,left:%(left)s,width:%(width)s,height:%(height)s}'
            % {'top': top, 'left': left, 'width': width, 'height': height},
        )

    def tearDown(self):
        screenshot_path = '/'.join([
            settings.STATICFILES_DIRS[0],
            self.get_screenshot_path()
        ])
        self.driver.save_screenshot(screenshot_path)
        self.driver.quit()

    def get_screenshot_path(self):
        return 'images/screenshots/%s.png' % self.save_as
