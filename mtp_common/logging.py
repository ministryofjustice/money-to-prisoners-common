import json
import logging


class ELKFormatter(logging.Formatter):
    """
    Formats log records as JSON for shipping to ELK
    """

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, 'asctime'):
            record.asctime = self.formatTime(record, self.datefmt)
        log = {
            'timestamp': record.asctime,
            'timestamp_msec': record.created * 1000,
            'message': record.getMessage(),
            'variables': record.args,
            '@fields.level': record.levelname or 'NONE',
            '@fields.logger': 'app-%s' % record.name or 'unknown',
            '@fields.source_path': '%s#%s' % (record.pathname or '?', record.lineno or '0'),
        }

        if record.exc_info:
            if not record.exc_text:
                # Cache the traceback like super method
                try:
                    record.exc_text = self.formatException(record.exc_info)
                except (AttributeError, TypeError):
                    record.exc_text = str(record.exc_info)
            log['@fields.exception'] = record.exc_text

        if hasattr(record, 'elk_fields') and isinstance(record.elk_fields, dict):
            # additional fields can be added to LogRecord in an `elk_fields` dict
            # ensure that any data passed can be json-serialised
            log.update(record.elk_fields)

        return json.dumps(log, default=str, ensure_ascii=False)
