from __future__ import annotations
from contextvars import ContextVar
from typing import Optional

# Create request and trace ids
_request_id: ContextVar[Optional[str]] = ContextVar("_request_id", default=None)
_trace_id: ContextVar[Optional[str]] = ContextVar("_trace_id", default=None)

def set_request_id(request_id: str) -> None:
    _request_id.set(request_id)

def get_request_id() -> Optional[str]:
    return _request_id.get()

def clear_request_id() -> None:
    _request_id.set(None)

def set_trace_id(trace_id: str) -> None:
    _trace_id.set(trace_id)

def get_trace_id() -> Optional[str]:
    return _trace_id.get()

def clear_trace_id() -> None:
    _trace_id.set(None)
