Money to Prisoners
==================

A Django app containing utilities and tools common to all Money to Prisoners services/applications.

Features
--------

* REST utilities for retrieving information from `money-to-prisoners-api`_
* Integration and accessibility testing with selenium
* Python code style testing
* Log formatting for shipping to ELK

Usage
-----

Add ``money-to-prisoners-utils==<version>`` to the Money to Prisoners application's requirements.txt.
There are two variations as setuptools *extras*:

* Use ``money-to-prisoners-utils[testing]==<version>`` for environments requiring testing
* Use ``money-to-prisoners-utils[monitoring]==<version>`` for the deployed version

Developing
----------

* Test using ``python setup.py test`` or ``./run_tests.py [arguments]``
* Update VERSION tuple in ``mtp_utils/__init__.py``
* Git tag with version
* Submit to PyPi with ``python setup.py sdist bdist_wheel upload``


.. _money-to-prisoners-api: https://github.com/ministryofjustice/money-to-prisoners-api
