import collections
import functools
import logging
import os
import socket
import types
import unittest
from urllib.parse import urlparse, urljoin

from django.conf import settings
from django.template.loader import render_to_string
from django.test import LiveServerTestCase
from django.utils.deprecation import MiddlewareMixin
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webelement import WebElement

from mtp_common.test_utils.webdrivers import get_web_driver

logger = logging.getLogger('mtp')


class WebDriverControlMixin:

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
            '//*[@type="submit" and @value="' + text + '"]'
        ).click()

    def click_on_text_substring(self, text):
        """
        Click on an input or element containing specified text
        """
        self.driver.find_element_by_xpath(
            '//*[text()[contains(.,"' + text + '")]] | '
            '//*[@type="submit" and @value[contains(.,"' + text + '")]]'
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


class FunctionalTestCase(LiveServerTestCase, WebDriverControlMixin):
    """
    Used for integration/functional testing of MTP client applications
    """
    auto_load_test_data = False
    required_webdrivers = None
    test_accessibility = False
    accessibility_scope_selector = None
    accessibility_standard = None

    @classmethod
    def _databases_names(cls, include_mirrors=True):
        # MTP client applications do not have databases
        if len(settings.DATABASES):
            return super()._databases_names(include_mirrors=include_mirrors)
        return []

    @classmethod
    def setUpClass(cls):
        if 'RUN_FUNCTIONAL_TESTS' not in os.environ:
            raise unittest.SkipTest('functional tests are disabled')

        remote_url = os.environ.get('DJANGO_TEST_REMOTE_INTEGRATION_URL', None)
        if remote_url:
            # do not start separate LiveServerThread
            super(LiveServerTestCase, cls).setUpClass()
            cls.live_server_url = remote_url
        else:
            super(FunctionalTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        remote_url = os.environ.get('DJANGO_TEST_REMOTE_INTEGRATION_URL', None)
        if remote_url:
            cls._tearDownClassInternal()
            super(LiveServerTestCase, cls).tearDownClass()
        else:
            super(FunctionalTestCase, cls).tearDownClass()

    def setUp(self):
        if self.auto_load_test_data:
            self.load_test_data()

        web_driver = os.environ.get('WEBDRIVER', 'chrome-headless')
        if self.required_webdrivers and web_driver not in self.required_webdrivers:
            self.skipTest('this test requires %s' % ' or '.join(self.required_webdrivers))
        try:
            self.driver = get_web_driver(web_driver)
        except ValueError as e:
            self.fail(str(e))

        if self.test_accessibility:
            self.setup_accessibility_run()

    def tearDown(self):
        self.driver.quit()

    def load_test_data(self, command=None):
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
                sock.sendall(command or b'load_test_data')
                response = sock.recv(1024).strip()
            if response != b'done':
                logger.error('Test data not reloaded!')
        except OSError:
            logger.exception('Error communicating with test server controller socket')

    def enable_accessibility(self):
        """
        Turns on accessibility assertions for functional test methods.
        This method runs once for a test case instance.
        """
        self.test_accessibility = True

        def decorate_test(func):
            @functools.wraps(func)
            def decorated_test(test_case_self, *args, **kwargs):
                current_standard = AccessibilityTestingMiddleware.standard
                override_standard = getattr(func, '__accessibility_standard', self.accessibility_standard)
                if override_standard:
                    AccessibilityTestingMiddleware.standard = override_standard
                result = func(*args, **kwargs)
                test_case_self.assertAccessible()
                if override_standard:
                    AccessibilityTestingMiddleware.standard = current_standard
                return result

            return decorated_test

        for attr in dir(self):
            if not attr.startswith('test_'):
                continue
            test_method = getattr(self, attr)
            if not callable(test_method) or getattr(test_method, '__disable_accessibility', False):
                continue
            setattr(self, attr, types.MethodType(decorate_test(test_method), self))

    def setup_accessibility_run(self):
        """
        Turns on accessibility testing for each test run enabling web driver to run additional javascript.
        NB: currently, only some explicit calls to the web driver (e.g. get) will cause accessibility checks,
        so call self.assertAccessible() at strategic locations to force accessibility testing
        """
        self.audits = collections.OrderedDict()

        execute_func = self.driver.execute
        navigation_commands = {
            Command.GET,
            Command.GO_BACK, Command.GO_FORWARD, Command.REFRESH,
            Command.CLICK_ELEMENT, Command.SUBMIT_ELEMENT,
        }
        key_commands = {Command.SEND_KEYS_TO_ELEMENT, Command.SEND_KEYS_TO_ACTIVE_ELEMENT}
        submit_keys = {Keys.RETURN, Keys.ENTER}

        @functools.wraps(execute_func)
        def wrapped_execute(web_driver_self, driver_command, params=None):
            result = execute_func(driver_command, params=params)
            if driver_command in navigation_commands or \
                    driver_command in key_commands and any(key in params.get('value', []) for key in submit_keys):
                url = web_driver_self.current_url
                if url not in self.audits:
                    script = 'return getAccessibilityAudit("%s");' % (self.accessibility_scope_selector or '')
                    audit = web_driver_self.execute_script(script)
                    self.audits[url] = audit
            return result

        self.driver.execute = types.MethodType(wrapped_execute, self.driver)

    # Assertions

    def assertInSource(self, search, msg=None):  # noqa: N802
        """
        Searches the page source for text or a regular expression
        """
        if hasattr(search, 'search'):
            self.assertTrue(search.search(self.driver.page_source), msg=msg)
        else:
            self.assertIn(search, self.driver.page_source, msg=msg)

    def assertNotInSource(self, search, msg=None):  # noqa: N802
        """
        Searches the page source to ensure it doesn't contain text or a regular expression
        """
        if hasattr(search, 'search'):
            self.assertFalse(search.search(self.driver.page_source), msg=msg)
        else:
            self.assertNotIn(search, self.driver.page_source, msg=msg)

    def assertCssProperty(self, selector, property, expected_value):  # noqa: N802
        element = self.driver.find_element_by_css_selector(selector)
        self.assertEqual(expected_value, element.value_of_css_property(property))

    def _current_url_matches(self, expected_url, ignore_query_string=True):
        current_url = self.driver.current_url
        if ignore_query_string:
            current_url = current_url.split('?')[0]
        if hasattr(expected_url, 'search'):
            return bool(expected_url.search(current_url))
        else:
            expected_url = urljoin(self.live_server_url, expected_url)
            return expected_url == current_url

    def assertCurrentUrl(self, expected_url, ignore_query_string=True, msg=None):  # noqa: N802
        """
        Checks the current page url matches expected url or regular expression
        """
        msg = (msg if msg is not None
               else "Expected URL '%s' does not match actual URL '%s'" % (expected_url, self.driver.current_url))
        return self.assertTrue(self._current_url_matches(expected_url, ignore_query_string=ignore_query_string),
                               msg=msg)

    def assertNotCurrentUrl(self, expected_url, ignore_query_string=True, msg=None):  # noqa: N802
        """
        Checks the current page url does not match expected url or regular expression
        """
        msg = (msg if msg is not None
               else "Expected URL '%s' matches actual URL '%s'" % (expected_url, self.driver.current_url))
        return self.assertFalse(self._current_url_matches(expected_url, ignore_query_string=ignore_query_string),
                                msg=msg)

    def assertAccessible(self):  # noqa: N802
        """
        Checks accessibility audit
        """

        def htmlcs_code(code):
            try:
                parts = code.split('.')
                standard = parts[0]
                criterion = '.'.join(parts[3].split('_')[:3])
                techniques = parts[4].replace(',', ', ')
                return '%s §%s %s' % (standard, criterion, techniques)
            except IndexError:
                return code

        messages = []
        for url, audit in self.audits.items():
            axs_audit = audit['axs']
            htmlcs_audit = audit['htmlcs']
            issues = len(axs_audit) + len(htmlcs_audit)
            if not issues:
                continue

            message = 'Page at %s has %d accessibility issue%s' % (
                url, issues, '' if issues == 1 else 's',
            )
            if axs_audit:
                message += '\n\nGoogle Accessibility Tools:'
                for issue in axs_audit:
                    message += '\n- %(severity)s: %(message)s (%(code)s)' % issue
                    for element in issue.get('elements', []):
                        message += '\n  %s' % element
            if htmlcs_audit:
                message += '\n\nHTML Code Sniffer:'
                for issue in htmlcs_audit:
                    issue['code'] = htmlcs_code(issue['code'])
                    message += '\n- %(message)s (%(code)s)' \
                               '\n  %(element)s' % issue

            messages.append(message)
        if messages:
            self.fail('\n\n'.join(messages))


def enable_accessibility(suite):
    """
    Wraps tests in a suite such that subclasses of FunctionalTestCase
    perform accessibility testing each time get is called on the web driver
    :param suite: the unittest.TestSuite to wrap
    """
    for test_case in suite:
        if isinstance(test_case, unittest.TestSuite):
            enable_accessibility(test_case)
        elif isinstance(test_case, FunctionalTestCase):
            test_case.enable_accessibility()


def disable_accessibility(method):
    """
    Remove automatic accessibility assertion at the end of the method
    :param method: test case method
    """
    method.__disable_accessibility = True
    return method


def override_accessibility_standard(standard):
    """
    Overrides the default accessibility testing standard
    :param standard: a standard supported by AccessibilityTestingMiddleware
    """

    def inner(method):
        method.__accessibility_standard = standard
        return method

    return inner


class AccessibilityTestingMiddleware(MiddlewareMixin):
    """
    View processing middleware to insert accessibility testing code into the HTML
    """
    standard = 'WCAG2AA'  # WCAG2A, WCAG2AA, WCAG2AAA, Section508

    def process_response(self, request, response):
        if response and response.status_code == 200:
            content = response.content
            a11y_template = render_to_string('mtp_common/a11y.html', {
                'include_warnings': False,
                'standard': self.standard
            })
            a11y_template = a11y_template.encode(response.charset)
            content = content.replace(b'</body>', a11y_template + b'\n</body>', 1)
            response.content = content

        return response
