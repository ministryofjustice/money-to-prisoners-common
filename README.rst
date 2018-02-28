Money to Prisoners
==================

A Django app containing utilities and assets common to all Money to Prisoners services/applications.

Features
--------

* Reusable templates for form fields and errors
* Base sass and static assets
* Base templates
* Authentication utilities and views for connecting to the MTP api
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

Add url patterns:

.. code-block:: python

    from django.conf.urls import url

    from mtp_common.auth import views

    urlpatterns = [
        url(r'^login/$', views.login, {
            'template_name': 'login.html',
            }, name='login'),
        url(
            r'^logout/$', views.logout, {
                'template_name': 'login.html',
                'next_page': reverse_lazy('login'),
            }, name='logout'
        ),
    ]

Configure Django settings:

.. code-block:: python

    MIDDLEWARE = (
        ...
        # instead of django.middleware.csrf.CsrfViewMiddleware
        'mtp_common.auth.csrf.CsrfViewMiddleware',
        ...
        # instead of django.contrib.auth.middleware.AuthenticationMiddleware
        'mtp_common.auth.middleware.AuthenticationMiddleware',
        ...
    )

    AUTHENTICATION_BACKENDS = (
        'mtp_common.auth.backends.MojBackend',
    )

    CSRF_FAILURE_VIEW = 'mtp_common.auth.csrf.csrf_failure'

If you wish for additional interface methods, you can extend ``mtp_common.auth.models.MojUser``,
and specify your subclass as ``MOJ_USER_MODEL``. An example would be adding a property to
access a key in the ``user_data`` dict.

.. code-block:: python

    MOJ_USER_MODEL = 'myapp.models.MyCustomUser'

Specify the parameters of the API authentication. ``API_CLIENT_ID`` and ``API_CLIENT_SECRET``
should be unique to your application.

.. code-block:: python

    API_CLIENT_ID = 'xxx'
    API_CLIENT_SECRET = os.environ.get('API_CLIENT_SECRET', 'xxx')
    API_URL = os.environ.get('API_URL', 'http://localhost:8000')

    OAUTHLIB_INSECURE_TRANSPORT = True

Developing
----------

.. image:: https://travis-ci.org/ministryofjustice/money-to-prisoners-common.svg?branch=master
    :target: https://travis-ci.org/ministryofjustice/money-to-prisoners-common

* Test using ``./run.py test`` or ``python setup.py test``
* Update the version with ``./run.py set_version --version [?.?.?]``
* Commit and push changes to github
* Submit to PyPi with ``./run.py upload``

Translating
-----------

Update translation files with ``./run.py make_messages`` – you need to do this every time any translatable text is updated.

Compile messages ``./run.py compile_messages`` – only needed during local testing or development, it happens automatically during build or upload.

Pull updates from Transifex with ``./run.py translations --pull``. You'll need to update translation files afterwards and manually check that the merges occurred correctly.

Push latest English to Transifex with ``./run.py translations --push``. NB: you should pull updates before pushing to merge correctly.

Common assets
-------------

All shared assets used for `money-to-prisoners-cashbook`_, `money-to-prisoners-bank-admin`_,
`money-to-prisoners-prisoner-location-admin`_ and `money-to-prisoners-send-money`_ are kept in this package.

Each application’s build scripts install this package automatically.

SCSS, JavaScript, images
------------------------

Assets that need compiling are in ``mtp_common/assets-src/(images|javascripts|scss)``.
The base sass file, ``_mtp.scss``, is used to include the sass includes from this packge into each frontend app.

Static assets are in ``mtp_common/static/(images|javascripts|css)``.

There is a `separate guide to the various visual elements`_
defined in this repository and used by the various MTP apps.

Django templates
----------------

Common templates used by the client applications are kept in ``mtp_common/templates``.

.. _separate guide to the various visual elements: mtp_common/docs/README.md
.. _money-to-prisoners-api: https://github.com/ministryofjustice/money-to-prisoners-api
.. _money-to-prisoners-cashbook: https://github.com/ministryofjustice/money-to-prisoners-cashbook
.. _money-to-prisoners-bank-admin: https://github.com/ministryofjustice/money-to-prisoners-bank-admin
.. _money-to-prisoners-prisoner-location-admin: https://github.com/ministryofjustice/money-to-prisoners-prisoner-location-admin
.. _money-to-prisoners-send-money: https://github.com/ministryofjustice/money-to-prisoners-send-money
