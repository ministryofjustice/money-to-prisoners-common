import importlib
import os

from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

VERSION = importlib.import_module('mtp_user_admin').VERSION

with open('README.rst') as readme:
    README = readme.read()

install_requires = [
    'Django>=1.9,<1.10',
]

setup(
    name='money-to-prisoners-user-admin',
    version=str(VERSION),
    author='Ministry of Justice Digital Services',
    url='https://github.com/ministryofjustice/money-to-prisoners-user-admin',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    license='MIT',
    description='Django app for user account administration in Money to Prisoners',
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
)
