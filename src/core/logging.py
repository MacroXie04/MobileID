import json
import logging
from contextvars import ContextVar

request_id_context = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Attach the current request id to log records."""

    def filter(self, record):
        record.request_id = request_id_context.get()
        return True


class JsonFormatter(logging.Formatter):
    """Small JSON log formatter for production stdout logs."""

    def format(self, record):
        payload = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
