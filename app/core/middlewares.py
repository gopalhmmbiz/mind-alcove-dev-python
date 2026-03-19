# core/middleware/auth.py
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.responses import ErrorResponse
from app.core.context import request_id_context


# Not in use
async def auth_middleware(request: Request, call_next):
    # Skip auth for health check
    if request.url.path == "/api/health":
        return await call_next(request)

    # Check for static API key in headers
    secret_from_header = request.headers.get("x-api-key")

    if not secret_from_header:
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(message="Missing API key in headers").model_dump()
        )

    if secret_from_header != settings.secret_key:
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(message="Invalid API key").model_dump()
        )

    # Proceed to next middleware / route
    response = await call_next(request)
    return response


async def request_id_middleware(request: Request, call_next):
    # 1. Generate a unique ID
    request_id = str(uuid.uuid4())

    # 2. Set the context (returns a token used for cleanup)
    token = request_id_context.set(request_id)

    try:
        # 3. Proceed to the router/service
        response = await call_next(request)

        return response
    finally:
        # 4. Clean up the context after the request is done
        request_id_context.reset(token)
