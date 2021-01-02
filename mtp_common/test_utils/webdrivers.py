import os
import sys
import stat
import tarfile
import tempfile
from urllib.parse import urljoin
import zipfile

import requests
from selenium import webdriver


def get_download_path():
    path = os.path.join(sys.prefix, 'lib', 'selenium')
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def make_executable(path):
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


class ChromeConf:
    base_url = 'http://chromedriver.storage.googleapis.com/'

    def __init__(self, version=None, platform=None):
        self.version = version or self.latest_version
        self.platform = platform or self.default_platform
        self.executable_path = os.path.join(get_download_path(), 'chromedriver')

    def load_driver(self, headless=True, width=1280, height=800):
        if not os.path.exists(self.executable_path):
            self.download_binary()
        options = webdriver.ChromeOptions()
        if os.geteuid() == 0 or os.path.exists('/.dockerenv'):
            options.add_argument('no-sandbox')
        options.add_argument('window-size=%d,%d' % (width, height))
        if headless:
            options.add_argument('force-device-scale-factor=1')
        options.headless = headless
        return webdriver.Chrome(executable_path=self.executable_path, chrome_options=options)

    @property
    def latest_version(self):
        return requests.get(urljoin(self.base_url, 'LATEST_RELEASE')).text.strip()

    @property
    def default_platform(self):
        if sys.platform.startswith('linux'):
            return 'linux64'
        elif sys.platform == 'darwin':
            return 'mac64'
        else:
            raise RuntimeError('Cannot determine platform on %s' % sys.platform)

    def download_binary(self):
        download_url = urljoin(self.base_url, '%s/chromedriver_%s.zip' % (self.version, self.platform))
        print('Downloading chromedriver %s %s' % (self.version, self.platform))
        with tempfile.TemporaryFile() as temp, open(self.executable_path, 'wb') as driver_path:
            r = requests.get(download_url)
            if not r.status_code == 200:
                raise RuntimeError('Could not download %s' % download_url)
            temp.write(r.content)
            temp.seek(0)
            z = zipfile.ZipFile(temp)
            driver_path.write(z.read('chromedriver'))
        make_executable(self.executable_path)


class FirefoxConf:
    def __init__(self, version=None, platform=None):
        self.version = version or self.latest_version
        self.platform = platform or self.default_platform
        self.executable_path = os.path.join(get_download_path(), 'geckodriver')

    def load_driver(self, headless=True, width=1280, height=800):
        if not os.path.exists(self.executable_path):
            self.download_binary()
        options = webdriver.FirefoxOptions()
        options.add_argument('--window-size=%d,%d' % (width, height))
        options.headless = headless
        return webdriver.Firefox(executable_path=self.executable_path, options=options)

    @property
    def latest_version(self):
        releases = requests.get('https://api.github.com/repos/mozilla/geckodriver/releases').json()
        return releases[0]['tag_name']

    @property
    def default_platform(self):
        if sys.platform.startswith('linux'):
            return 'linux64'
        elif sys.platform == 'darwin':
            return 'macos'
        else:
            raise RuntimeError('Cannot determine platform on %s' % sys.platform)

    def download_binary(self):
        download_url = 'https://github.com/mozilla/geckodriver/releases/download/' \
                       '%(version)s/geckodriver-%(version)s-%(platform)s.tar.gz' % {
                           'version': self.version,
                           'platform': self.platform,
                       }
        print('Downloading geckodriver %s %s' % (self.version, self.platform))
        with tempfile.NamedTemporaryFile() as temp, open(self.executable_path, 'wb') as driver_path:
            r = requests.get(download_url)
            if not r.status_code == 200:
                raise RuntimeError('Could not download %s' % download_url)
            temp.write(r.content)
            temp.seek(0)
            z = tarfile.open(temp.name)
            driver_path.write(z.extractfile('geckodriver').read())
        make_executable(self.executable_path)


web_drivers = {
    'chrome': (ChromeConf, {'headless': False}),
    'chrome-headless': (ChromeConf, {'headless': True}),
    'firefox': (FirefoxConf, {'headless': False}),
    'firefox-headless': (FirefoxConf, {'headless': True}),
}


def get_web_driver(driver_name):
    conf = web_drivers.get(driver_name)
    if not conf:
        raise ValueError('Unknown driver: %s' % driver_name)
    conf_cls, kwargs = conf
    return conf_cls().load_driver(**kwargs)
