Money to Prisoners
==================

A Django app containing utilities and tools common to all Money to Prisoners services/applications.

Features
--------

* Reusable templates for form fields and errors
* REST utilities for retrieving information from `money-to-prisoners-api`_
* Integration and accessibility testing with selenium
* Python code style testing
* Log formatting for shipping to ELK

Usage
-----

Add ``money-to-prisoners-common==<version>`` to the Money to Prisoners application's requirements.txt.
There are two variations as setuptools *extras*:

* Use ``money-to-prisoners-common[testing]==<version>`` for environments requiring testing
* Use ``money-to-prisoners-common[monitoring]==<version>`` for the deployed version

Developing
----------

* Test using ``python setup.py test`` or ``./run_tests.py [arguments]``
* Update VERSION tuple in ``mtp_common/__init__.py``
* Git tag with version
* Submit to PyPi with ``python setup.py sdist bdist_wheel upload``


.. _money-to-prisoners-api: https://github.com/ministryofjustice/money-to-prisoners-api

# Money to Prisoners Common Assets

All assets used for [money-to-prisoners-cashbook](), [money-to-prisoners-prisoner-location-admin](https://github.com/ministryofjustice/money-to-prisoners-prisoner-location-admin/), [money-to-prisoners-bank-admin](https://github.com/ministryofjustice/money-to-prisoners-bank-admin/) are kept in this package.

They are included into each application using [npm](http://npmjs.com/). Each application's build scripts run npm automatically.

### Sass, Javascript, Images

Static assets are in `./assets/(images|javascripts|scss)`. The base sass file, [`_mtp.scss`](https://github.com/ministryofjustice/money-to-prisoners-common/blob/master/assets/scss/_mtp.scss), is used to include the sass includes from this packge into each frontend app.

### Django templates

Common templates used across all 3 applications are kept in `./templates/`. They are made accessible to each application by adding the path to the bower package to the template directories list in `settings.py`.

This repository has a dependency on [mojular/moj-elements](https://github.com/mojular/moj-elements), which provides the assets and scripts for MOJ sites. The [mojular](https://github.com/mojular/) repositories are shared across multiple departments, and any change should be checked by members of the organization.
