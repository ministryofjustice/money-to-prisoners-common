import importlib
import os
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 5):
    raise SystemError('Python version must be at least 3.5')

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

__version__ = importlib.import_module('mtp_common').__version__

with open('README.rst') as readme:
    README = readme.read()

install_requires = [
    'Django>=2.2,<2.3',
    'django-form-error-reporting>=0.9',
    'django-widget-tweaks>=1.4,<1.5',
    'django-zendesk-tickets>=0.14',
    'pytz>=2019.1',
    'requests>=2.18,<3',
    'requests-oauthlib>=1,<2',
    'slumber>=0.7,<0.8',
    'selenium>=3.11,<4',
    'transifex-client>=0.13,<0.14',
    'govuk-bank-holidays>=0.3',
    'cryptography>=2.3,<3',
    'PyJWT>=1.7,<2',
    'kubernetes>=11,<12',  # corresponds to server version 1.15
    'prometheus_client>=0.6,<1',
]
extras_require = {
    'monitoring': [
        'sentry_sdk==0.16.5',
    ],
    'testing': [
        'flake8>=3.7,<4',
        'pep8-naming>=0.8.2,<1',
        'flake8-bugbear>=19.3,<20',
        'flake8-quotes>=2.0.1,<3',
        'flake8-blind-except>=0.1.1,<1',
        'flake8-debugger>=3.1,<4',
        'responses>=0.10,<1',
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
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=extras_require['testing'],
    test_suite='run.test',
)
