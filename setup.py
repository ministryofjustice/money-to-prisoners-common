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
    'Django>=5.2.7,<5.3',

    'django-widget-tweaks>=1.5,<1.6',
    'notifications-python-client>=10,<11',
    'requests~=2.32',
    'requests-oauthlib~=2.0',
    'slumber>=0.7,<0.8',
    'selenium~=4.38',
    'cryptography>=46',
    'boto3~=1.40',
    # corresponds to server version 1.32 (minor version skew should be within ±1 of cluster)
    # https://github.com/kubernetes-client/python#compatibility-matrix-of-supported-client-versions
    'kubernetes~=32.0',
    'opencensus~=0.11',
    'opencensus-ext-azure~=1.1',
    'opencensus-ext-django~=0.8',
    'prometheus-client~=0.23',
    'sentry-sdk~=2.42',
    'libsass~=0.23',
    'uWSGI~=2.0.31',

    # moj-built dependencies (should be locked versions)
    'django-moj-irat==0.11',
    'django-zendesk-tickets==0.19',
    'govuk-bank-holidays==0.17',
]
extras_require = {
    'testing': [
        # third-party dependencies (versions should be flexible to allow for bug fixes)
        'flake8~=7.3',
        'flake8-blind-except~=0.2.1',
        'flake8-bugbear~=25.10',
        # 'flake8-commas~=4.0',
        'flake8-debugger~=4.1',
        # 'flake8-logging~=1.8',
        'flake8-quotes~=3.4',
        'pep8-naming~=0.15',
        'responses~=0.25',
        'twine~=6.2',
        'watchdog~=6.0',
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
