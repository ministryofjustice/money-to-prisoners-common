import importlib
import os
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 8):
    raise SystemError('Python version must be at least 3.8')

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

__version__ = importlib.import_module('mtp_common').__version__

with open('README.rst') as readme:
    README = readme.read()

install_requires = [
    # third-party dependencies (versions should be flexible to allow for bug fixes)
    'Django>=2.2,<2.3',  # mtp apps are only compatible with django 2.2
    'django-extended-choices>=1.3,<2',
    'django-widget-tweaks>=1.4,<1.5',
    'notifications-python-client~=6.3',
    'pytz>=2022.1',
    'requests>=2.27,<3',
    'requests-oauthlib>=1,<2',
    'slumber>=0.7,<0.8',
    'selenium~=4.0',
    'transifex-client>=0.14,<0.15',
    'cryptography>=36,<37',
    'boto3>=1.18.32,<1.21.0',
    'kubernetes~=21.0',  # corresponds to server version 1.21 (matching `live` cluster)
    'prometheus-client>=0.14,<1',
    'sentry-sdk~=1.5',
    'libsass~=0.21',
    'uWSGI~=2.0.20',

    # moj-built dependencies (should be locked versions)
    'django-form-error-reporting==0.10',
    'django-moj-irat==0.7',
    'django-zendesk-tickets==0.15',
    'govuk-bank-holidays==0.11',
]
extras_require = {
    'testing': [
        # third-party dependencies (versions should be flexible to allow for bug fixes)
        'flake8~=4.0',
        'flake8-blind-except~=0.2.1',
        'flake8-bugbear~=22.0',
        'flake8-debugger~=4.0',
        'flake8-quotes~=3.3.1',
        'pep8-naming~=0.12.0',
        'responses~=0.21.0',
        'twine~=4.0',
        'watchdog~=2.1',
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
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=extras_require['testing'],
    test_suite='run.test',
)
