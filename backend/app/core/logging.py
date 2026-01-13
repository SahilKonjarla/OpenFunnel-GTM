from __future__ import annotations
import logging
import sys
from datetime import datetime as dt, timezone
from app.core.config import settings
from app.core.request_context import get_request_id, get_trace_id

class ContextFilter(logging.Filter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service
        record.env = settings.app_env
        record.request_id = get_request_id() or ""
        record.trace_id = get_trace_id() or ""
        return True

class KeyValueFormattter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        # ISO timestamp
        ts = dt.now(timezone.utc).isoformat(timespec="milliseconds")
        msg = record.getMessage()
        event = getattr(record, "event", "-")
        base = (
            f"ts={ts} level={record.levelname}"
            f" service={getattr(record, 'service', '-')}"
            f" env={getattr(record, 'env', '-')}"
            f" event={event}"
            f" request_id={getattr(record, 'request_id', '-')}"
            f" trace_id={getattr(record, 'trace_id', '-')}"
        )

        # include logger name and the message
        out = f"{base} logger= {record.name} msg={msg}"

        # include exception error message if it exists
        if record.exc_info:
            out += f" exc={self.formatException(record.exc_info)}"

        return out

def init_logging(service_name: str) -> None:
    root = logging.getLogger()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)

    # prevent double handlers if reloaded
    if getattr(root, "_openfunnel_configured", False):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(KeyValueFormattter())
    handler.addFilter(ContextFilter(service_name))

    root.addHandler(handler)
    root._openfunnel_configured = True

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
