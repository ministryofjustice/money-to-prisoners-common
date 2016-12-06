from contextlib import contextmanager
import logging


@contextmanager
def silence_logger(name='mtp', level=logging.CRITICAL):
    logger = logging.getLogger(name)
    old_level = logger.level
    logger.setLevel(level)
    yield
    logger.setLevel(old_level)
