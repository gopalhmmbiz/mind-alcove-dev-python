from contextvars import ContextVar
from typing import Optional

# This variable will be unique to each concurrent request
request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)