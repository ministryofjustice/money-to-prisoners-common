import json
import logging
from logging.config import dictConfig
import unittest

messages = []


def get_log_text():
    return '\n'.join(messages)


class Handler(logging.Handler):
    def __init__(self, level=0):
        super().__init__(level)

    def emit(self, record):
        msg = self.format(record)
        messages.append(msg)


class ELKLoggingTestCase(unittest.TestCase):
    @classmethod
    def setup_logging(cls, formatter='elk'):
        logging_conf = {
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'simple': {
                    'format': '%(asctime)s [%(levelname)s] %(message)s',
                    'datefmt': '%Y-%m-%dT%H:%M:%S',
                },
                'elk': {
                    '()': 'mtp_common.logging.ELKFormatter'
                }
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'tests.test_logging.Handler',
                    'formatter': formatter,
                },
            },
            'root': {
                'level': 'WARNING',
                'handlers': ['console'],
            },
            'loggers': {
                'mtp': {
                    'level': 'INFO',
                    'handlers': ['console'],
                    'propagate': False,
                },
            },
        }

        dictConfig(logging_conf)
        messages.clear()

    def test_elk_fields_not_formatted_normally(self):
        self.setup_logging(formatter='simple')

        mtp_logger = logging.getLogger('mtp')
        root_logger = logging.getLogger()
        for logger in [mtp_logger, root_logger]:
            logger.info(
                'Test info message',
                extra={
                    'excluded': 321,
                    'elk_fields': {
                        '@fields.extra_field': 123
                    }
                }
            )
        logs = get_log_text()
        self.assertIn('Test info message', logs)
        self.assertNotIn('elk_fields', logs)
        self.assertNotIn('extra_field', logs)
        self.assertNotIn('123', logs)
        self.assertNotIn('excluded', logs)

    def test_elk_formatter_includes_extra_fields(self):
        self.setup_logging(formatter='elk')

        mtp_logger = logging.getLogger('mtp')
        mtp_logger.info(
            'Test info message',
            extra={
                'excluded': 321,
                'elk_fields': {
                    '@fields.extra_field': 123,
                    '@fields.extra_field2': ['a', 'b'],
                }
            }
        )
        logs = get_log_text()
        logs = json.loads(logs)
        self.assertIsInstance(logs, dict)
        for key in ['timestamp_msec', 'message',
                    '@fields.level', '@fields.logger', '@fields.source_path',
                    '@fields.extra_field']:
            self.assertIn(key, logs)
        self.assertEqual(logs['message'], 'Test info message')
        self.assertEqual(logs['@fields.level'], 'INFO')
        self.assertEqual(logs['@fields.extra_field'], 123)
        self.assertEqual(logs['@fields.extra_field2'], ['a', 'b'])
        self.assertNotIn('excluded', logs)

    def test_elk_formatter_serialises_arguments(self):
        class Obj:
            def __str__(self):
                return '🌍'

        self.setup_logging(formatter='elk')

        mtp_logger = logging.getLogger('mtp')
        mtp_logger.info('This %d object cannot be serialised to JSON: %s', 1, Obj())
        logs = get_log_text()
        logs = json.loads(logs)
        self.assertIsInstance(logs, dict)
        self.assertEqual(logs['message'], 'This 1 object cannot be serialised to JSON: 🌍')
        self.assertSequenceEqual(logs['variables'], [1, '🌍'])
