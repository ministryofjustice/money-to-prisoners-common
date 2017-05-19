import importlib
import os
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 4):
    raise SystemError('Python version must be at least 3.4')

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

__version__ = importlib.import_module('mtp_common').__version__

with open('README.rst') as readme:
    README = readme.read()

install_requires = [
    'Django>=1.10,<1.11',
    'django-form-error-reporting>=0.6',
    'django-widget-tweaks>=1.4,<1.5',
    'django-zendesk-tickets>=0.10',
    'pytz>=2016.7',
    'requests-oauthlib>=0.6,<0.7',
    'slumber>=0.7,<0.8',
    'selenium>=3.0,<3.1',
    'transifex-client>=0.12,<0.13',
    'govuk-bank-holidays==0.1',
    'cryptography==1.7.2',
    'PyJWT==1.4.2',
]
extras_require = {
    'monitoring': [
        'raven>=6.0,<6.1',
    ],
    'testing': [
        'flake8>=3.2,<3.3',
        'pep8-naming>=0.4,<0.5',
        'responses>=0.5,<0.6',
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
    description='Django app with common code and assets for Money to Prisoners serivces',
    long_description=README,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=extras_require['testing'],
    test_suite='run.test',
)
