# core/security/api_key.py
from fastapi import Security
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.exceptions import AppException

api_key_header = APIKeyHeader(
    name="x-api-key",
    auto_error=False,
)

async def require_secret_key(api_key: str = Security(api_key_header)) -> None:
    if not api_key:
        raise AppException(
            message="Missing API key in headers",
            status_code=401,
        )

    if api_key != settings.secret_key:
        raise AppException(
            message="Invalid API key",
            status_code=403,
        )
