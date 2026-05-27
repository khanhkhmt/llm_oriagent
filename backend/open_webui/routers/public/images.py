"""
Public Image Generation API — POST /images/generations
Only enabled when ENABLE_IMAGE_GENERATION=true.
"""
import logging, time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.routers.public.deps import PublicAPIContext, get_public_api_context
from open_webui.routers.public.rate_limit import check_rate_limit
from open_webui.routers.public.schemas import (
    PublicImageGenerationRequest, PublicImageGenerationResponse, PublicImageData,
)

log = logging.getLogger(__name__)
router = APIRouter()

@router.post("/images/generations", response_model=PublicImageGenerationResponse,
    summary="Generate images", description="Generate images from a text prompt. Only available when image generation is enabled.")
async def public_generate_images(request: Request, form_data: PublicImageGenerationRequest,
    ctx: PublicAPIContext = Depends(get_public_api_context)):
    await check_rate_limit(request, ctx.user_id, "images_generations", ctx.request_id)
    if not request.app.state.config.ENABLE_IMAGE_GENERATION:
        raise HTTPException(status_code=403, detail="Image generation is not enabled.")
    if form_data.n < 1 or form_data.n > 4:
        raise HTTPException(status_code=400, detail="Parameter 'n' must be between 1 and 4.")
    if not form_data.prompt or not form_data.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required.")
    # Validate size format
    if form_data.size and "x" not in form_data.size:
        raise HTTPException(status_code=400, detail="Size must be in format 'WIDTHxHEIGHT' (e.g. '1024x1024').")
    from open_webui.models.users import Users
    user = await Users.get_user_by_id(ctx.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    try:
        from open_webui.routers.images import image_generations, CreateImageForm
        internal_form = CreateImageForm(
            model=form_data.model,
            prompt=form_data.prompt,
            size=form_data.size,
            n=form_data.n,
        )
        result = await image_generations(request, internal_form, user=user)
        images = [PublicImageData(url=img.get("url", "")) for img in result] if isinstance(result, list) else []
        log.info("Public image gen: req=%s user=%s count=%d", ctx.request_id, ctx.user_id, len(images))
        return PublicImageGenerationResponse(created=int(time.time()), data=images)
    except HTTPException:
        raise
    except Exception as e:
        log.error("Public image gen error: req=%s error=%s", ctx.request_id, str(e))
        raise HTTPException(status_code=500, detail="Image generation failed.")
