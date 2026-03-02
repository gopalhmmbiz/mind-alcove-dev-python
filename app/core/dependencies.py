# core/security/api_key.py
import hmac
import hashlib
import time

from fastapi import Security, Request
from fastapi.security import APIKeyHeader

from app.cache.factory import get_cache
from app.core.config import settings
from app.core.exceptions import AppException

api_key_header = APIKeyHeader(
    name="x-api-key",
    auto_error=False,
)

# not in use
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


timestamp_header = APIKeyHeader(name="X-Timestamp", auto_error=False)
signature_header = APIKeyHeader(name="X-Signature", auto_error=False)

async def verify_signature(
    timestamp: str = Security(timestamp_header),
    signature: str = Security(signature_header)
) -> None:
    # 1. Check if headers exist
    if not timestamp:
        raise AppException(status_code=401, message="Missing timestamp in header.")
    if not signature:
        raise AppException(status_code=401, message="Missing signature in header.")

    # 2. Check expiration timestamp valid or not
    try:
        time_diff = abs(int(time.time()) - int(timestamp))
        if time_diff > settings.s2s_token_ttl:
            raise AppException(status_code=401, message="Request expired")
    except ValueError:
        raise AppException(status_code=400, message="Invalid timestamp format")

    # 3. verify the signature and compare
    expected_signature = hmac.new(
        settings.secret_key.encode(),
        timestamp.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise AppException(status_code=403, message="Invalid signature")


class RateLimiter:
    def __init__(self, times: int, seconds: int):
        """
        Args:
            times (int): Maximum number of requests allowed.
            seconds (int): Time window in seconds.
        """
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request):
        # 1. Identify User (Strictly requires X-User-ID)
        user_id = request.headers.get("X-User-ID")

        if not user_id:
            raise AppException(
                status_code=400,
                message="User identification header (X-User-ID) is required for this endpoint."
            )

        cache = get_cache()

        # 2. Create a unique key
        path = request.url.path
        key = f"rl:{user_id}:{path}"

        # 3. Increment the counter (Atomic)
        current_hits = await cache.increment(key)

        # 4. Set TTL on the very first hit
        if current_hits == 1:
            await cache.set(key, current_hits, ttl=self.seconds)

        # 5. Check if limit exceeded
        if current_hits > self.times:
            raise AppException(
                status_code=429,
                message=f"Take a breath! Limit exceeded. Maximum {self.times} requests per {self.seconds}s."
            )
