Money to Prisoners Common
=========================

This version of `money-to-prisoners-common` is using Django 3.2 and is currently
experimental.

A Django app containing utilities and assets common to all Prisoner Money applications.

.. image:: https://circleci.com/gh/ministryofjustice/money-to-prisoners-common.svg?style=svg
    :target: https://circleci.com/gh/ministryofjustice/money-to-prisoners-common

Features
--------

* Build pipeline CLI with actions that can depend on others (inspired by invoke/fabric)
* Base SCSS, JS and static assets
* Base templates for staff and public apps
* Build action to include GOV.UK Design System assets
* Reusable templates for form fields and errors
* Authentication utilities and views for connecting to `money-to-prisoners-api`_
* User account management forms and views
* REST utilities for communicating with `money-to-prisoners-api`_
* Utility for communicating with HMPPS Prison API (NOMIS)
* Integration and accessibility testing with selenium
* Python code style testing
* Log formatting for shipping to ELK
* Cookie management tools to anonymise users and allow them to opt in
* Prometheus metrics view providing app version information
* Constants shared between apps
* Email sending using GOV.UK Notify

Usage
-----

This is not a standalone Django application and is included as a requirement of Prisoner Money apps.

* Make code changes and add any tests necessary
* Test using ``./run.py test`` or ``python setup.py test``
* Bump the package version with ``./run.py bump_version [--major | --minor | --patch]``
* Submit to PyPi by:

  * making a new release on Github (package version comes from the code, not Github release title)
  * or ``./run.py upload`` locally (if release cannot be made on Github for some reason)

Add or update ``money-to-prisoners-common~=<major version>.<minor version>.0`` to the app’s requirements base.txt.
There is an additional variant installed as a setuptools *extra*:
Use ``money-to-prisoners-common[testing]~=<major version>.<minor version>.0`` for environments requiring testing;
this is placed into the app’s requirements dev.txt.
Incrementing the build/patch version is used to push minor fixes so these above requirements will automatically include them.

While making changes to this library, you can install it locally in "editable" mode.
See ``python_dependencies --common-path …`` build task.

Translating
-----------

Update translation files with ``./run.py make_messages`` – you need to do this every time any translatable text is updated.

Compile messages ``./run.py compile_messages`` – only needed during local testing or development, it happens automatically during build or upload.

Requires [transifex cli tool](https://github.com/transifex/cli#installation) for synchronisation:

Pull updates from Transifex with ``./run.py translations --pull``.
You’ll need to update translation files afterwards and manually check that the merges occurred correctly.

Push latest English to Transifex with ``./run.py translations --push``.
NB: you should pull updates before pushing to merge correctly.

Assets
------

All shared assets used by Prisoner Money apps are kept in this package.
Each app’s build scripts install this package automatically which also bring in the GOV.UK Design System.

Assets that need compiling are in ``mtp_common/assets-src/mtp_common``.
Static assets are in ``mtp_common/static/mtp_common``.

Common templates used by the client apps are kept in ``mtp_common/templates/(govuk-frontend|mtp_common)``.
The ones in ``govuk-frontend`` are essentially translated from the GOV.UK Design System whereas those in ``mtp_common``
are custom components or are heavily modified.

Local Development Environment
-----------------------------

Prisoner Money apps can be run natively (i.e. directly by python on your machine) or using docker-compose.
Using docker-compose is perhaps the easiest way to bring up all Prisoner Money apps in concert,
but it requires access to the private `money-to-prisoners-deploy`_ infrastructure.
However, when editing this common library, it’s easier to run them natively
because this package can be installed in "editable" mode.

Check out each app and helper repository side-by-side in one directory using git:

* `money-to-prisoners-api`_
* `money-to-prisoners-cashbook`_
* `money-to-prisoners-bank-admin`_
* `money-to-prisoners-noms-ops`_
* `money-to-prisoners-emails`_
* `money-to-prisoners-transaction-uploader`_ – NB: this app does not expose a web interface
* `money-to-prisoners-send-money`_
* `money-to-prisoners-start-page`_
* `money-to-prisoners-common`_
* `money-to-prisoners-deploy`_ – NB: this is a private repository

**Running natively (does not require access to the private deploy repository)**

Each app describes its own installation in its read-me file, but here’s a quick guide:

1. Setup local postgres database server. There’s no need to create a user or database if using default settings.

2. Install python version 3.10.

3. Install nodejs version 20.

4. Setup a python virtual environment for each app. These are used to isolate python dependency libraries for each app.

   1. You can either make one directly in *each* repository directory:

   .. code-block:: sh

     python3 -m venv venv

   2. Or install and use `virtualenvwrapper`_ which allows activating a virtual environment by name from any location.
      This option is particularly helpful for git hooks or when you normally run the apps in docker-compose.
      In the directory containing all repos:

   .. code-block:: sh

     for app in api cashbook bank-admin noms-ops transaction-uploader send-money start-page deploy; do
       cd money-to-prisoners-$app
       mkvirtualenv -a . money-to-prisoners-$app
       [[ -f requirements/dev.txt ]] && pip install -r requirements/dev.txt
       [[ -f requirements.txt ]] && pip install -r requirements.txt
       cd -
     done
     cd money-to-prisoners-common
     mkvirtualenv -a . money-to-prisoners-common
     pip install -e '.[testing]'

5. Run the apps. The ``api`` always needs to be running when any of the other apps are used other than ``start-page``.

   .. code-block:: sh

     cd <app repository root>
     # activate the virtual environment if one was made directly
     . venv/bin/activate
     # OR activate the virtual environment using virtualenvwrapper
     workon money-to-prisoners-<app name>

     # run the app
     ./run.py serve
     # OR if it’s the api, this automatically alternative also creates a fresh database with sample data
     ./run.py start --test-mode

After this has been done once, bringing up apps again only requires repeating step 5.

**Running using docker-compose (requires access to the private deploy repository)**

1. Get access to `money-to-prisoners-deploy`_ and see read-me inside to unlock it.

2. Setup local environment:

   1. Get the docker registry address of ECR used for deployed environment in Cloud Platform. In the ``deploy`` repo:

   .. code-block:: sh

     ./manage.py config docker-login  # log docker into ECR
     ./manage.py app ci-settings [any mtp app name]  # note the $ECR_REGISTRY value

   Alternatively, this value can be derived from the ``ecr`` kubernetes secret in the production namespace in Cloud Platform.
   Use the value of ``repo_url`` up to the first ``/``.

   2. Create a ``.env`` file in this repository’s root directory adding this ``ECR_REGISTRY`` value:

   .. code-block::

     ECR_REGISTRY=?????????.amazonaws.com

3. Pull images from private docker registry in Cloud Platform. In the ``deploy`` repo:

.. code-block:: sh

  ./manage.py config docker-login  # only necessary if not done above
  ./manage.py image pull-ecr

4. Launch all apps in concert. In this repo:

.. code-block:: sh

  docker-compose up

   NB: The newer ``docker compose up`` form only works after the ``docker-compose up`` has already built the containers the first time!

5. Create standard users and populate database with sample data. In this repo:

.. code-block:: sh

  docker-compose exec api ./manage.py load_test_data

After this has been done once, bringing up the full stack in future only requires running ``docker-compose up``
or ``docker compose up`` in this repo. Deleting docker images, containers or volumes will require repeating steps 3 to 5.

If you run into issues with the dockerised development environment, the following troubleshooting steps should reset the state:

* Shutdown existing docker-compose containers, and remove volumes/networks/images with ``docker-compose down -v --rmi all`` from this repo’s root directory (note this will wipe your local database, omit the ``-v`` to prevent this)
* Pull fresh base images (step 3 above)
* Rebuild the app images without cache via ``docker-compose build --no-cache`` from this repo’s root directory
* Restart the apps in the background via ``docker-compose up -d`` from this repo’s root directory
* Tail the logs at your leisure via ``docker-compose logs <app>`` from money-to-prisoners-common root directory

**Accessing the apps**

Irrespective of how the apps were run, those exposing a web interface will be accessible:

* api: http://localhost:8000/admin/
* cashbook: http://localhost:3001/
* bank-admin: http://localhost:3002/
* noms-ops: http://localhost:3003/
* send-money: http://localhost:3004/
* start-page: http://localhost:8005/

You can find login details in `load_test_data.py`_

Caveat: You can only log into one app at a time locally because the cookies within which the session is stored are namespaced to domain only.

Additional Bespoke Packages
---------------------------

There are several dependencies of the ``money-to-prisoners-common`` python library which are maintained by this team, so they may require code-changes when the dependencies (e.g. Django) of the ``money-to-prisoners-common`` python library, or any of the Prisoner Money apps, are incremented.

* `django-zendesk-tickets`_
* `govuk-bank-holidays`_

There are additional bespoke dependencies defined as python dependencies within the Prisoner Money apps.



.. Links referenced in document above:
.. _money-to-prisoners-api: https://github.com/ministryofjustice/money-to-prisoners-api
.. _money-to-prisoners-cashbook: https://github.com/ministryofjustice/money-to-prisoners-cashbook
.. _money-to-prisoners-bank-admin: https://github.com/ministryofjustice/money-to-prisoners-bank-admin
.. _money-to-prisoners-noms-ops: https://github.com/ministryofjustice/money-to-prisoners-noms-ops
.. _money-to-prisoners-transaction-uploader: https://github.com/ministryofjustice/money-to-prisoners-transaction-uploader
.. _money-to-prisoners-send-money: https://github.com/ministryofjustice/money-to-prisoners-send-money
.. _money-to-prisoners-start-page: https://github.com/ministryofjustice/money-to-prisoners-start-page
.. _money-to-prisoners-common: https://github.com/ministryofjustice/money-to-prisoners-common
.. _money-to-prisoners-deploy: https://github.com/ministryofjustice/money-to-prisoners-deploy
.. _money-to-prisoners-emails: https://github.com/ministryofjustice/money-to-prisoners-emails
.. _load_test_data.py: https://github.com/ministryofjustice/money-to-prisoners-api/blob/a6e039a3fc85d675c62658c226a3bd94d27355d5/mtp_api/apps/core/management/commands/load_test_data.py#L221-L229
.. _django-zendesk-tickets: https://github.com/ministryofjustice/django-zendesk-tickets
.. _govuk-bank-holidays: https://github.com/ministryofjustice/govuk-bank-holidays
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/
