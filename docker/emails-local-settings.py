# Unlike docker/no-local-settings.py (used by every other app), this file is NOT empty.
#
# money-to-prisoners-emails's callbacks.views.NotifyCallbackView rejects any request where
# request.is_secure() is False. In real test/parity/prod this is already True without any
# Django-level config - the ingress/uwsgi layer sets the WSGI environ's scheme directly (verified
# empirically - a plain HTTP request to the real test environment already gets past this check) -
# but locally there's no such proxy in front of this container, so it's always False, and the
# Playwright emails-api specs can never pass.
#
# SECURE_PROXY_SSL_HEADER tells Django to also trust an X-Forwarded-Proto header, which the
# Playwright suite sends itself here to stand in for a real ingress. This lives only in
# money-to-prisoners-common (never touches money-to-prisoners-emails) and only loads inside
# this container, via the bind-mount in docker-compose.yml - it has no effect on
# money-to-prisoners-emails's own settings, tests, or any real deployed environment.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

