import glob
import logging
import os
import socket
import unittest
from urllib.parse import urlparse

from django.conf import settings
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger('mtp')


@unittest.skipUnless('RUN_FUNCTIONAL_TESTS' in os.environ, 'functional tests are disabled')
class FunctionalTestCase(LiveServerTestCase):
    """
    Used for integration/functional testing of MTP client applications
    """
    auto_load_test_data = False
    required_webdriver = None

    @classmethod
    def _databases_names(cls, include_mirrors=True):
        # MTP client applications do not have databases
        if len(settings.DATABASES):
            return super()._databases_names(include_mirrors=include_mirrors)
        return []

    @classmethod
    def setUpClass(cls):
        remote_url = os.environ.get('DJANGO_TEST_REMOTE_INTEGRATION_URL', None)
        if remote_url:
            # do not start separate LiveServerThread
            super(LiveServerTestCase, cls).setUpClass()
            cls.live_server_url = remote_url
        else:
            super(FunctionalTestCase, cls).setUpClass()

    def setUp(self):
        if self.auto_load_test_data:
            self.load_test_data()

        web_driver = os.environ.get('WEBDRIVER', 'phantomjs')
        if self.required_webdriver and web_driver != self.required_webdriver:
            raise unittest.SkipTest('%s webdriver required for this test' % self.required_webdriver)
        if web_driver == 'firefox':
            fp = webdriver.FirefoxProfile()
            fp.set_preference('browser.startup.homepage', 'about:blank')
            fp.set_preference('startup.homepage_welcome_url', 'about:blank')
            fp.set_preference('startup.homepage_welcome_url.additional', 'about:blank')
            self.driver = webdriver.Firefox(firefox_profile=fp)
        elif web_driver == 'chrome':
            paths = glob.glob('./node_modules/selenium-standalone/.selenium/chromedriver/*-chromedriver')
            paths = filter(lambda path: os.path.isfile(path) and os.access(path, os.X_OK),
                           paths)
            try:
                self.driver = webdriver.Chrome(executable_path=next(paths))
            except StopIteration:
                self.fail('Cannot find Chrome driver')
        elif web_driver == 'phantomjs':
            path = './node_modules/phantomjs/lib/phantom/bin/phantomjs'
            self.driver = webdriver.PhantomJS(executable_path=path)
        else:
            self.fail('Unknown webdriver %s' % web_driver)

        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1000, 1000)

    def tearDown(self):
        self.driver.quit()

    def load_test_data(self):
        """
        Sends a command to the API controller port to reload test data
        """
        logger.info('Reloading test data')
        try:
            with socket.socket() as sock:
                sock.connect((
                    urlparse(settings.API_URL).netloc.split(':')[0],
                    int(os.environ.get('CONTROLLER_PORT', 8800))
                ))
                sock.sendall(b'load_test_data')
                response = sock.recv(1024).strip()
            if response != b'done':
                logger.error('Test data not reloaded!')
        except OSError:
            logger.exception('Error communicating with test server controller socket')

    # Assertions

    def assertInSource(self, search):  # noqa
        """
        Searches the page source for text or a regular expression
        """
        if hasattr(search, 'search'):
            self.assertTrue(search.search(self.driver.page_source))
        else:
            self.assertIn(search, self.driver.page_source)

    def assertNotInSource(self, search):  # noqa
        """
        Searches the page source to ensure it doesn't contain text or a regular expression
        """
        if hasattr(search, 'search'):
            self.assertFalse(search.search(self.driver.page_source))
        else:
            self.assertNotIn(search, self.driver.page_source)

    # Helper methods

    def scroll_to_top(self):
        """
        Scrolls the page to the top
        """
        self.driver.execute_script('window.scrollTo(0, 0);')

    def scroll_to_bottom(self):
        """
        Scrolls the page to the bottom
        """
        self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

    def get_element(self, specifier):
        """
        Returns a single element specified by xpath, css selector or id
        """
        if not specifier or isinstance(specifier, WebElement):
            return specifier
        if any(char in specifier for char in ['/', '@']):
            # assume specifer is xpath
            return self.driver.find_element_by_xpath(specifier)
        if any(char in specifier for char in ['.', '#']):
            # assume specifier is css selector
            return self.driver.find_element_by_css_selector(specifier)
        return self.driver.find_element_by_id(specifier)

    def type_in(self, specifier, text, send_return=False):
        """
        Enter text into an element specified by xpath, css selector or id
        """
        element = self.get_element(specifier)
        if send_return:
            text += Keys.RETURN
        element.send_keys(text)

    def click_on_text(self, text):
        """
        Click on an input or element containing specified text
        """
        self.driver.find_element_by_xpath(
            '//*[text() = "' + text + '"] | '
            '//input[@type="submit" and @value="' + text + '"]'
        ).click()

    def login(self, username, password, url=None,
              username_field='id_username', password_field='id_password'):
        """
        Fill in login form
        """
        self.driver.get(url or self.live_server_url)
        self.type_in(username_field, username)
        self.type_in(password_field, password, send_return=True)

    def fill_in_form(self, data):
        """
        Fill in a form with keys being used as element specifiers and values as the text
        NB: currently not set up to work with check boxes or radio inputs
        """
        for specifier, text in data.items():
            self.type_in(specifier, text)
