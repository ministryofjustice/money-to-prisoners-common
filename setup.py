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
    'Django>=5.1.7,<5.2',

    'django-widget-tweaks>=1.5,<1.6',
    'notifications-python-client>=10,<11',
    'requests~=2.32',
    'requests-oauthlib~=2.0',
    'slumber>=0.7,<0.8',
    'selenium~=4.24',
    'cryptography>=43',
    'boto3~=1.35',
    'kubernetes~=29.0',  # corresponds to server version 1.29 (minor version skew should be within ±1 of cluster)
    'opencensus~=0.11',
    'opencensus-ext-azure~=1.1',
    'opencensus-ext-django~=0.8',
    'prometheus-client>=0.20,<1',
    'sentry-sdk~=2.13',
    'libsass~=0.23',
    'uWSGI~=2.0.26',

    # moj-built dependencies (should be locked versions)
    'django-moj-irat==0.10',
    'django-zendesk-tickets==0.18',
    'govuk-bank-holidays==0.15',
]
extras_require = {
    'testing': [
        # third-party dependencies (versions should be flexible to allow for bug fixes)
        'flake8~=7.1',
        'flake8-blind-except~=0.2.1',
        'flake8-bugbear~=24.8',
        # 'flake8-commas~=4.0',
        'flake8-debugger~=4.1',
        # 'flake8-logging~=1.6',
        'flake8-quotes~=3.4',
        'pep8-naming~=0.14.1',
        'responses~=0.25',
        'twine~=5.1',
        'watchdog~=5.0',
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
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.12',
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=extras_require['testing'],
    test_suite='run.test',
)
