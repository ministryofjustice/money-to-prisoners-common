Money to Prisoners
==================

A Django app containing utilities and assets common to all Money to Prisoners services/applications.

Features
--------

* Reusable templates for form fields and errors
* Base sass and static assets
* Base templates
* User account management forms and views
* REST utilities for retrieving information from `money-to-prisoners-api`_
* Integration and accessibility testing with selenium
* Python code style testing
* Log formatting for shipping to ELK

Usage
-----

Add ``money-to-prisoners-common==<version>`` to the Money to Prisoners application’s requirements.txt.
There are two variations as setuptools *extras*:

* Use ``money-to-prisoners-common[testing]==<version>`` for environments requiring testing
* Use ``money-to-prisoners-common[monitoring]==<version>`` for the deployed version

Developing
----------

* Test using ``python setup.py test`` or ``./run_tests.py [arguments]``
* Update VERSION tuple in ``mtp_common/__init__.py``
* Git tag with version
* Submit to PyPi with ``python setup.py sdist bdist_wheel upload``

Common assets
=============

All shared assets used for `money-to-prisoners-cashbook`_, `money-to-prisoners-bank-admin`_,
`money-to-prisoners-prisoner-location-admin`_ and `money-to-prisoners-send-money`_ are kept in this package.

Each application’s build scripts install this package automatically.

This repository has a dependency on `mojular/moj-elements`_, which provides the assets and scripts for MOJ sites.
The `mojular`_ repositories are shared across multiple departments, and any change should be checked by members of the organization.

Sass, javascript, images
------------------------

Assets that need compiling are in ``mtp_common/assets/(images|javascripts|scss)``.
The base sass file, ``_mtp.scss``, is used to include the sass includes from this packge into each frontend app.

Static assets are in ``mtp_common/static/(images|javascripts|css)``.

Django templates
----------------

Common templates used by the client applications are kept in ``mtp_common/templates``.


.. _money-to-prisoners-api: https://github.com/ministryofjustice/money-to-prisoners-api
.. _money-to-prisoners-cashbook: https://github.com/ministryofjustice/money-to-prisoners-cashbook
.. _money-to-prisoners-bank-admin: https://github.com/ministryofjustice/money-to-prisoners-bank-admin
.. _money-to-prisoners-prisoner-location-admin: https://github.com/ministryofjustice/money-to-prisoners-prisoner-location-admin
.. _money-to-prisoners-send-money: https://github.com/ministryofjustice/money-to-prisoners-send-money
.. _mojular: https://github.com/mojular
.. _mojular/moj-elements: https://github.com/mojular/moj-elements
