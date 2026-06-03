"""
Public Models API — GET /models
Lists models the authenticated user is allowed to access.
"""

import logging
import time

from fastapi import APIRouter, Depends, Request

from open_webui.routers.public.deps import PublicAPIContext, get_public_api_context
from open_webui.routers.public.rate_limit import check_rate_limit
from open_webui.routers.public.schemas import (
    PublicModel,
    PublicModelCapabilities,
    PublicModelListResponse,
)
from open_webui.utils.models import get_all_models, get_filtered_models

log = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/models",
    response_model=PublicModelListResponse,
    summary="List available models",
    description="Returns a list of models the authenticated API key user is allowed to use.",
    responses={
        401: {"description": "Invalid or missing API key"},
        403: {"description": "API key feature disabled or insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def list_models(
    request: Request,
    ctx: PublicAPIContext = Depends(get_public_api_context),
):
    await check_rate_limit(request, ctx.user_id, "models", ctx.request_id)

    start = time.monotonic()

    # Reuse internal model listing logic
    from open_webui.models.users import Users

    user = await Users.get_user_by_id(ctx.user_id)
    if user is None:
        return PublicModelListResponse(object="list", data=[])

    # Get all models via existing infrastructure
    all_models = await get_all_models(request, user=user)

    # Filter to only models user can access
    filtered = await get_filtered_models(all_models, user)

    # Convert to public schema — strip internal details
    public_models = []
    for model in filtered:
        # Determine provider
        provider = ""
        if model.get("owned_by") == "ollama":
            provider = "ollama"
        elif model.get("owned_by") == "openai" or model.get("openai"):
            provider = "openai"
        elif model.get("owned_by") == "arena":
            provider = "arena"
        elif model.get("pipe"):
            provider = "pipeline"
        else:
            provider = model.get("owned_by", "unknown")

        # Skip filter pipelines
        if "pipeline" in model and model["pipeline"].get("type") == "filter":
            continue

        # Determine capabilities from model info (defensive: any level may be None)
        info = model.get("info") or {}
        meta = info.get("meta") or {}
        capabilities = meta.get("capabilities") or {}

        public_models.append(
            PublicModel(
                id=model.get("id", ""),
                name=model.get("name", model.get("id", "")),
                provider=provider,
                capabilities=PublicModelCapabilities(
                    vision=capabilities.get("vision", False),
                    tools=capabilities.get("tools", False),
                    file_upload=capabilities.get("file_upload", False),
                ),
            )
        )

    latency_ms = int((time.monotonic() - start) * 1000)
    log.info(
        "Public API models: request_id=%s user_id=%s count=%d latency_ms=%d",
        ctx.request_id,
        ctx.user_id,
        len(public_models),
        latency_ms,
    )

    return PublicModelListResponse(object="list", data=public_models)
