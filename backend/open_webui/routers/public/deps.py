"""
Authentication and context dependencies for OriAgent Public API.
Reuses the existing API key (sk-...) infrastructure from open_webui.utils.auth.
"""

import logging
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from open_webui.models.users import Users
from open_webui.utils.access_control import has_permission

log = logging.getLogger(__name__)

bearer_security = HTTPBearer(auto_error=False)


class PublicAPIContext(BaseModel):
    """Context object passed to every authenticated Public API endpoint."""

    user_id: str
    role: str
    request_id: str
    scopes: list[str] = []
    api_key_id: Optional[str] = None


def _generate_request_id(request: Request) -> str:
    """
    Use client-supplied X-Request-ID if present, otherwise generate one.
    Also stores it on request.state for exception handlers.
    """
    client_id = request.headers.get("X-Request-ID", "")
    request_id = client_id if client_id else f"req_{uuid.uuid4().hex[:16]}"
    request.state.public_request_id = request_id
    return request_id


async def get_public_api_context(
    request: Request,
    auth_token: HTTPAuthorizationCredentials = Depends(bearer_security),
) -> PublicAPIContext:
    """
    Dependency that authenticates a Public API request via API key.

    Requirements:
    1. Authorization: Bearer <api_key> header is required.
    2. API key must start with 'sk-' and map to a valid user.
    3. User must have role 'user' or 'admin'.
    4. API key feature must be enabled.
    5. Endpoint restrictions are enforced if enabled.

    Returns a PublicAPIContext with user info and request_id.
    """
    request_id = _generate_request_id(request)

    # --- Extract token ---
    token: Optional[str] = None
    if auth_token is not None:
        token = auth_token.credentials

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide Authorization: Bearer <api_key>",
        )

    # --- Must be an API key (sk-...) ---
    if not token.startswith("sk-"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format. API key must start with 'sk-'.",
        )

    # API key feature is always enabled for OriAgent Public API

    # --- Look up user by API key ---
    user = await Users.get_user_by_api_key(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    # --- Check user role ---
    if user.role not in {"user", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. User role must be 'user' or 'admin'.",
        )

    # --- Check endpoint restriction if enabled ---
    if request.app.state.config.ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS:
        allowed_paths = [
            path.strip()
            for path in str(request.app.state.config.API_KEYS_ALLOWED_ENDPOINTS).split(",")
            if path.strip()
        ]
        request_path = request.url.path
        is_allowed = any(
            request_path == allowed or request_path.startswith(allowed + "/")
            for allowed in allowed_paths
        )
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint is not allowed for API key access.",
            )

    # API key usage is permitted for all users

    # --- Update last active ---
    await Users.update_last_active_by_id(user.id)

    # --- Log access (safe fields only) ---
    log.info(
        "Public API access: request_id=%s user_id=%s role=%s method=%s path=%s",
        request_id,
        user.id,
        user.role,
        request.method,
        request.url.path,
    )

    return PublicAPIContext(
        user_id=user.id,
        role=user.role,
        request_id=request_id,
        scopes=[],  # TODO: Implement scope-based permissions
        api_key_id=None,  # API key ID tracking can be added later
    )


def get_public_request_id(request: Request) -> str:
    """
    Dependency for unauthenticated endpoints that still need a request_id.
    """
    return _generate_request_id(request)
