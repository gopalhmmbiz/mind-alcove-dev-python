# core/middleware/auth.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.responses import ErrorResponse


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
