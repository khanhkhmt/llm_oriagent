"""
OriAgent Public API v1 — Main Router
Aggregates all public API sub-routers under a single router.
Mounted at /api/public/v1 in main.py.
"""

import logging
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from open_webui.routers.public.deps import get_public_request_id
from open_webui.routers.public.schemas import PublicHealthResponse

from open_webui.routers.public import models as models_module
from open_webui.routers.public import chat as chat_module
from open_webui.routers.public import files as files_module
from open_webui.routers.public import audio as audio_module
from open_webui.routers.public import knowledge as knowledge_module
from open_webui.routers.public import images as images_module

log = logging.getLogger(__name__)

router = APIRouter()


# ─── Health Check (no auth required) ─────────────────────────────────────────

@router.get(
    "/health",
    response_model=PublicHealthResponse,
    summary="Health check",
    description="Check if the OriAgent Public API is operational. No authentication required.",
)
async def health_check(
    request: Request,
    request_id: str = Depends(get_public_request_id),
):
    return PublicHealthResponse(
        status="ok",
        service="OriAgent Public API",
        version="v1",
    )


# ─── Include sub-routers ─────────────────────────────────────────────────────

router.include_router(models_module.router, tags=["Public API - Models"])
router.include_router(chat_module.router, tags=["Public API - Chat"])
router.include_router(files_module.router, tags=["Public API - Files"])
router.include_router(audio_module.router, tags=["Public API - Audio"])
router.include_router(knowledge_module.router, tags=["Public API - Knowledge"])
router.include_router(images_module.router, tags=["Public API - Images"])
