Money to Prisoners
==================

A Django app containing utilities and assets common to all Money to Prisoners services/applications.

Features
--------

* Build pipeline with actions that depend on others
* Base SCSS, JS and static assets
* Base templates for staff and public apps
* Reusable templates for form fields and errors
* Authentication utilities and views for connecting to `money-to-prisoners-api`_
* User account management forms and views
* REST utilities for retrieving information from `money-to-prisoners-api`_
* Utility for communicating with NOMIS api
* Integration and accessibility testing with selenium
* Python code style testing
* Log formatting for shipping to ELK

Usage
-----

Add ``money-to-prisoners-common==<version>`` to the Money to Prisoners application’s requirements base.txt.
There is an additional variant installed as a setuptools *extra*:
Use ``money-to-prisoners-common[testing]==<version>`` for environments requiring testing; this is placed into
the application’s requirements dev.txt.

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

.. image:: https://circleci.com/gh/ministryofjustice/money-to-prisoners-common.svg?style=svg
    :target: https://circleci.com/gh/ministryofjustice/money-to-prisoners-common

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
`money-to-prisoners-noms-ops`_ and `money-to-prisoners-send-money`_ are kept in this package.

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
.. _money-to-prisoners-noms-ops: https://github.com/ministryofjustice/money-to-prisoners-noms-ops
.. _money-to-prisoners-send-money: https://github.com/ministryofjustice/money-to-prisoners-send-money

Development environment
-----------------------

There is a docker-compose for building and setting up the development environment. Steps are as follows:

1. Clone money-to-prisoners-common (if you haven't already):

.. code-block:: sh

    git clone https://github.com/ministryofjustice/money-to-prisoners-common.git money-to-prisoners-common

2. Change directory to the money-to-prisoners-common root directory (if you haven't already)

.. code-block:: sh

    cd money-to-prisoners-common

3. Clone the above directories as sibling directories to money-to-prisoners-common:

.. code-block:: sh

    git clone https://github.com/ministryofjustice/money-to-prisoners-api.git ../money-to-prisoners-api
    git clone https://github.com/ministryofjustice/money-to-prisoners-cashbook.git ../money-to-prisoners-cashbook
    git clone https://github.com/ministryofjustice/money-to-prisoners-bank-admin.git ../money-to-prisoners-bank-admin
    git clone https://github.com/ministryofjustice/money-to-prisoners-noms-ops.git ../money-to-prisoners-noms-ops
    git clone https://github.com/ministryofjustice/money-to-prisoners-send-money.git ../money-to-prisoners-send-money
    git clone https://github.com/ministryofjustice/money-to-prisoners-start-page.git ../money-to-prisoners-start-page
    git clone https://github.com/ministryofjustice/money-to-prisoners-transaction-uploader.git ../money-to-prisoners-transaction-uploader

4. Create a file called ``.env`` in money-to-prisoners-common root directory, add the variable ``ECR_ENDPOINT`` to this file in the format ``<key>=<value>``

5. Authenticate with the docker repository

.. code-block:: sh

    git clone https://github.com/ministryofjustice/money-to-prisoners-deploy.git ../money-to-prisoners-deploy
    cd ../money-to-prisoners-deploy
    ./manage.py config docker-login
    cd -

6. From ``money-to-prisoners-common`` root directory run ``docker-compose up``

7. (Optional) If you have not generated any data for the development environement, or if you have removed the docker volume associated with the database container, you will need to populate the database to be able to log into the services successfully. It will also create a minimal set of fake data to allow you to develop against existing data. However if you already have an existing docker volume with existing data, this command will delete that data.

To populate your database with fake data, run the following command from ``money-to-prisoners-common`` root directory, once the api container has started successfully

.. code-block:: sh

   docker-compose exec api ./manage.py load_test_data

You should then be able to access the services at the following URLs

* money-to-prisoners-api: http://localhost:8000
* money-to-prisoners-cashbook: http://localhost:8001
* money-to-prisoners-bank-admin: http://localhost:8002
* money-to-prisoners-noms-ops: http://localhost:8003
* money-to-prisoners-send-money: http://localhost:8004
* money-to-prisoners-start-page: http://localhost:8005

Caveats:

* You can only log into one service at a time, this is because the cookies within which the session is stored are namespaced to domain only (which is the desired behaviour for test/prod)

8. (Optional) If you want to set up some virtualenv's for money-to-prisoners, to help with things like running tests outside docker containers (e.g. as part of githooks), I would very much recommend using virtualenvwrapper. It's essentially a set of aliases that make managing virtualenv's a lot easier. See https://virtualenvwrapper.readthedocs.io/en/latest/install.html#basic-installation for installation instructions. Once you've got that installed, it's just a matter of running this command from the parent directory, that contains all of your checked-out ``money-to-prisoners-*`` repos:

.. code-block:: sh

    repos=(money-to-prisoners-api  money-to-prisoners-bank-admin  money-to-prisoners-cashbook  money-to-prisoners-deploy money-to-prisoners-noms-ops  money-to-prisoners-send-money  money-to-prisoners-transaction-uploader)
    for d in ${repos[@]}; do cd $d && mkvirtualenv -a . $d && pip install -r requirements/base.txt  -r requirements/dev.txt && cd -; done

Once you've run the above commands successfully, then to enter a virtual environment and at the same time ``cd`` into the directory of that repository, you can just run, for example:

.. code-block:: sh

    workon money-to-prisoners-api

Additional Bespoke Packages
---------------------------

There are several dependencies of the ``money-to-prisoners-common`` python library which are maintained by this team, so they may require code-changes when the dependencies (e.g. Django) of the ``money-to-prisoners-common`` python library, or any of the Prisoner Money services are incremented.

* django-form-error-reporting: https://github.com/ministryofjustice/django-form-error-reporting
* django-zendesk-tickets: https://github.com/ministryofjustice/django-zendesk-tickets
* govuk-bank-holidays: https://github.com/ministryofjustice/govuk-bank-holidays

There are additional bespoke dependencies defined as python dependencies within the Prisoner Money Services.
