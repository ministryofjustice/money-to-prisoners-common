# This file is deliberately empty.
#
# Each app's settings/base.py ends with `try: from .local import *`, so a developer's
# own settings/local.py is applied last and wins. That file is meant for running the app
# natively on the host, and local.py.sample points the database at 127.0.0.1.
#
# docker-compose bind-mounts each app repository into its container for live reload, which
# brings local.py in with it. The app then ignores DB_HOST=db and tries to reach postgres
# on 127.0.0.1 inside its own container, where nothing is listening.
#
# So docker-compose mounts this file over each app's settings/local.py. Local overrides for
# the containers belong in docker-compose.yml as environment variables instead, where they
# are visible to everyone rather than sitting in a gitignored file.
