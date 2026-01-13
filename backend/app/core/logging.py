from __future__ import annotations

import logging
import sys
from datetime import datetime as dt
from datetime import timezone

from ..core.config import settings
from ..core.request_context import get_request_id, get_trace_id

class ContextFilter(logging.Filter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.service_name = self.service_name
        record.env = settings.app_env
        record.request_id = get_request_id() or ""
        record.trace_id = get_trace_id() or ""
        return True

class KeyValueFormattter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        # ISO timestamp
        ts = dt.now(timezone.utc).isoformat(timespec="milliseconds")

        msg = record.getMessage()
        base = (
            f"ts={ts} level={record.levelname} service={getattr(record, 'service', '-')}"
            f" request_id={getattr(record, 'request_id', '-')} trace_id={getattr(record, 'trace_id', '-')}"
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
