import importlib
import os

from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

VERSION = importlib.import_module('mtp_utils').VERSION

with open('README.md') as readme:
    README = readme.read()

install_requires = [
    'Django>=1.9,<1.10',
]
extras_require = {
    'sentry': ['raven>=5.11'],
}
tests_require = []

setup(
    name='money-to-prisoners-utils',
    version=str(VERSION),
    author='Ministry of Justice Digital Services',
    url='https://github.com/ministryofjustice/money-to-prisoners-utils',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    license='MIT',
    description='Django app with shared utilities for Money to Prisoners serivces',
    long_description=README,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: MoJ Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=tests_require,
    test_suite='run_tests.run_tests',
)
