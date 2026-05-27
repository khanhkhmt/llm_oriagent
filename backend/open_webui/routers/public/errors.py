"""
Standardized error handling for OriAgent Public API.
All public API errors return a consistent JSON format with request_id.
"""

import logging
import traceback
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)


# ─── Error code mapping ──────────────────────────────────────────────────────
ERROR_TYPE_MAP = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    429: "rate_limit_error",
    500: "internal_error",
}


class PublicAPIError(HTTPException):
    """Custom exception for Public API endpoints with structured error response."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        request_id: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(status_code=status_code, detail=message)


def make_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str = "",
) -> JSONResponse:
    """Create a standardized error JSONResponse."""
    error_type = ERROR_TYPE_MAP.get(status_code, "internal_error")
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "type": error_type,
            },
            "request_id": request_id,
        },
    )


def make_success_response(data: dict, request_id: str = "") -> dict:
    """Create a standardized success response dict."""
    return {
        "success": True,
        "data": data,
        "request_id": request_id,
    }


async def public_api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for Public API routes.
    Ensures no stack traces are leaked to the client.
    """
    request_id = getattr(request.state, "public_request_id", "")

    if isinstance(exc, PublicAPIError):
        return make_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            request_id=request_id,
        )

    if isinstance(exc, HTTPException):
        code = ERROR_TYPE_MAP.get(exc.status_code, "internal_error")
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return make_error_response(
            status_code=exc.status_code,
            code=code,
            message=message,
            request_id=request_id,
        )

    # Unexpected errors — log but never expose stack trace
    log.error(
        "Public API unhandled error: request_id=%s path=%s error=%s",
        request_id,
        request.url.path,
        str(exc),
    )
    return make_error_response(
        status_code=500,
        code="internal_error",
        message="An internal error occurred. Please try again later.",
        request_id=request_id,
    )
