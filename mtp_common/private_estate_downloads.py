"""Issue and validate time-limited private estate download capabilities."""

import time

from django.core import signing


SALT = 'mtp.private-estate-download.v1'
PREFIX = 'private-estate-credits-v2/'
DEFAULT_RETENTION_SECONDS = 70 * 86400
LEGACY_LIFETIME_SECONDS = 70 * 86400


def issue_token(bucket_path, key, lifetime_seconds, retention_seconds=DEFAULT_RETENTION_SECONDS):
    if not key or not bucket_path.startswith(PREFIX):
        raise ValueError('A signing key and private estate object path are required')
    if (not isinstance(retention_seconds, int) or isinstance(retention_seconds, bool) or retention_seconds <= 0
            or not isinstance(lifetime_seconds, int) or isinstance(lifetime_seconds, bool)
            or not 0 < lifetime_seconds <= retention_seconds):
        raise ValueError('The link lifetime must be positive and no longer than the object retention period')
    return signing.dumps({'path': bucket_path, 'expires': int(time.time()) + lifetime_seconds},
                         key=key, salt=SALT, compress=True)


def read_token(token, key):
    if not key:
        raise signing.BadSignature('Download signing key is not configured')
    try:
        payload = signing.loads(token, key=key, salt=SALT, fallback_keys=[])
        path = payload['path']
        expires = payload['expires']
        if (not isinstance(path, str) or not path.startswith(PREFIX)
                or not isinstance(expires, int) or isinstance(expires, bool) or time.time() >= expires):
            raise ValueError
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise signing.BadSignature('Invalid or expired download token') from exc
    return path
