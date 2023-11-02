import importlib
import os

from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

__version__ = importlib.import_module('mtp_common').__version__

with open('README.rst') as readme:
    README = readme.read()

install_requires = [
    # third-party dependencies (versions should be flexible to allow for bug fixes)
    'Django>=3.2.23,<3.3',
    'django-widget-tweaks>=1.5,<1.6',
    'notifications-python-client~=8.1',
    'pytz>=2023.3',
    'requests~=2.31',
    'requests-oauthlib~=1.3',
    'slumber>=0.7,<0.8',
    'selenium~=4.15',
    'cryptography~=41.0',
    'boto3~=1.28',
    'kubernetes~=24.0',  # corresponds to server version 1.24 (within skew of `live` cluster)
    'opencensus~=0.11',
    'opencensus-ext-azure~=1.1',
    'opencensus-ext-django~=0.8',
    'prometheus-client>=0.18,<1',
    'sentry-sdk~=1.33',
    'libsass~=0.22',
    'uWSGI~=2.0.23',

    # moj-built dependencies (should be locked versions)
    'django-moj-irat==0.8',
    'django-zendesk-tickets==0.16',
    'govuk-bank-holidays==0.13',
]
extras_require = {
    'testing': [
        # third-party dependencies (versions should be flexible to allow for bug fixes)
        'flake8~=6.1',
        'flake8-blind-except~=0.2.1',
        'flake8-bugbear~=23.9',
        # 'flake8-commas~=2.1',
        'flake8-debugger~=4.1',
        # 'flake8-logging~=1.2',
        'flake8-quotes~=3.3',
        'pep8-naming~=0.13.3',
        'responses~=0.23.3',
        'twine~=4.0',
        'watchdog~=3.0',
    ],
}

setup(
    name='money-to-prisoners-common',
    version=__version__,
    author='Ministry of Justice Digital Services',
    url='https://github.com/ministryofjustice/money-to-prisoners-common',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    license='MIT',
    description='Django app with common code and assets for Money to Prisoners services',
    long_description=README,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.10',
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=extras_require['testing'],
    test_suite='run.test',
)
