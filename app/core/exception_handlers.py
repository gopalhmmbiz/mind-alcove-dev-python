from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.core.responses import ErrorResponse
from app.core.exceptions import AppException


def _format_validation_error(exc: RequestValidationError) -> str:
    """
    Converts FastAPI validation errors into a single rich string.

    Example:
    body -> prompt: field required | query -> limit: value is not a valid integer
    """
    formatted_errors: list[str] = []

    for error in exc.errors():
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg", "Invalid value")
        err_type = error.get("type", "")

        formatted_errors.append(
            f"{loc}: {msg}" + (f" ({err_type})" if err_type else "")
        )

    return " | ".join(formatted_errors)


def _app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.message
        ).model_dump()
    )


def _validation_exception_handler(request: Request, exc: RequestValidationError):
    message = _format_validation_error(exc)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            message=message
        ).model_dump()
    )


def _unhandled_exception_handler(request: Request, exc: Exception):
    # This catches literally everything else
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            message="Internal server error"
        ).model_dump()
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers all global exception handlers.
    Call this ONCE during app startup.
    """
    app.add_exception_handler(AppException, _app_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
