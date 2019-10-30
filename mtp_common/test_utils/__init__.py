from contextlib import contextmanager
from unittest import mock
import logging

from django.conf import settings
from django.core import cache as django_cache


@contextmanager
def silence_logger(name='mtp', level=logging.CRITICAL):
    logger = logging.getLogger(name)
    old_level = logger.level
    logger.setLevel(level)
    yield
    logger.setLevel(old_level)


@contextmanager
def local_memory_cache():
    """Configure settings.CACHES to use LocMemCache."""
    with mock.patch.dict(
        settings.CACHES['default'],
        {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    ):
        cache_handler = django_cache.CacheHandler()

        with mock.patch.object(django_cache, 'caches', cache_handler):
            try:
                yield
            finally:
                cache_handler['default'].clear()
