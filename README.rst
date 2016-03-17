Money to Prisoners
==================

A Django app containing utilities and tools common to the various Money to Prisoners services.
Currently, it is installed via ``pip`` in the client applications but not the api.

Features
--------

* REST utilities for retrieving information from `money-to-prisoners-api`_
* Integration testing with selenium
* Python code style testing

Usage
-----

Add ``money-to-prisoners-utils==[version]`` to the Money to Prisoners application's requirements.txt.

Developing
----------

* Test using ``python setup.py test`` or ``./run_tests.py [arguments]``
* Update VERSION in ``mtp_utils.__init__.py``
* Git tag with version
* Submit to PyPi with ``python setup.py sdist upload``


.. _money-to-prisoners-api: https://github.com/ministryofjustice/money-to-prisoners-api
