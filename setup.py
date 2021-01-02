import importlib
import os
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    raise SystemError('Python version must be at least 3.6')

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

__version__ = importlib.import_module('mtp_common').__version__

with open('README.rst') as readme:
    README = readme.read()

install_requires = [
    # third-party dependencies (versions should be flexible to allow for bug fixes)
    'Django>=2.2,<2.3',
    'django-widget-tweaks>=1.4,<1.5',
    'pytz>=2019.1',
    'requests>=2.18,<3',
    'requests-oauthlib>=1,<2',
    'slumber>=0.7,<0.8',
    'selenium>=3.11,<4',
    'transifex-client>=0.13,<0.14',
    'cryptography>=2.3,<3',
    'PyJWT>=1.7,<2',
    'kubernetes>=12,<13',  # corresponds to server version 1.16
    'prometheus_client>=0.6,<1',
    'sentry_sdk~=0.19.0',
    'libsass~=0.20',

    # moj-built dependencies (should be locked versions)
    'django-form-error-reporting==0.9',
    'django-zendesk-tickets==0.14',
    'govuk-bank-holidays==0.8',
]
extras_require = {
    'testing': [
        # third-party dependencies (versions should be flexible to allow for bug fixes)
        'flake8~=3.8.0',
        'pep8-naming~=0.11.0',
        'flake8-bugbear~=20.11',
        'flake8-quotes~=3.2',
        'flake8-blind-except~=0.1.1',
        'flake8-debugger~=4.0',
        'responses~=0.12.0',
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
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=extras_require['testing'],
    test_suite='run.test',
)
