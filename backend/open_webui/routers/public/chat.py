"""
Public Chat Completion API — POST /chat/completions
Provides OpenAI-compatible chat completion for third-party integrations.
Reuses the existing chat completion infrastructure without duplicating logic.
"""

import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from starlette.responses import StreamingResponse

from open_webui.routers.public.deps import PublicAPIContext, get_public_api_context
from open_webui.routers.public.rate_limit import check_rate_limit
from open_webui.routers.public.schemas import (
    PublicChatCompletionRequest,
    PublicChatCompletionResponse,
    PublicChatCompletionChoice,
    PublicChatCompletionChoiceMessage,
    PublicUsage,
)

from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.models import get_all_models, get_filtered_models

log = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/chat/completions",
    summary="Create a chat completion",
    description=(
        "Generates a chat completion response for the given messages and model. "
        "Compatible with OpenAI's chat completion API format. "
        "Supports both streaming (SSE) and non-streaming responses."
    ),
    responses={
        400: {"description": "Invalid request (bad model, missing messages, etc.)"},
        401: {"description": "Invalid or missing API key"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def public_chat_completions(
    request: Request,
    form_data: PublicChatCompletionRequest,
    ctx: PublicAPIContext = Depends(get_public_api_context),
):
    await check_rate_limit(request, ctx.user_id, "chat_completions", ctx.request_id)

    start = time.monotonic()

    # Get user object for internal APIs
    from open_webui.models.users import Users

    user = await Users.get_user_by_id(ctx.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    # Ensure models are loaded
    if not request.app.state.MODELS:
        await get_all_models(request, user=user)

    # Validate model exists and user has access
    model_id = form_data.model
    if model_id not in request.app.state.MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model '{model_id}' not found.",
        )

    # Check model access
    all_models = list(request.app.state.MODELS.values())
    filtered = await get_filtered_models(all_models, user)
    allowed_ids = {m.get("id") for m in filtered}

    if model_id not in allowed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have access to model '{model_id}'.",
        )

    # Build internal form_data — only safe parameters
    internal_form = {
        "model": model_id,
        "messages": [msg.model_dump() for msg in form_data.messages],
        "stream": form_data.stream,
    }

    if form_data.temperature is not None:
        internal_form["temperature"] = form_data.temperature
    if form_data.max_tokens is not None:
        internal_form["max_tokens"] = form_data.max_tokens
    if form_data.top_p is not None:
        internal_form["top_p"] = form_data.top_p
    if form_data.frequency_penalty is not None:
        internal_form["frequency_penalty"] = form_data.frequency_penalty
    if form_data.presence_penalty is not None:
        internal_form["presence_penalty"] = form_data.presence_penalty
    if form_data.stop is not None:
        internal_form["stop"] = form_data.stop

    # Add metadata — track external origin
    internal_form["metadata"] = {
        "user_id": ctx.user_id,
        "source": "public_api",
    }

    completion_id = f"chatcmpl_{uuid.uuid4().hex[:12]}"

    try:
        if form_data.stream:
            # Streaming response via SSE
            response = await generate_chat_completion(
                request=request,
                form_data=internal_form,
                user=user,
                bypass_filter=True,
            )

            if isinstance(response, StreamingResponse):
                # Wrap the internal stream to ensure OpenAI-compatible SSE format
                async def public_stream_wrapper():
                    try:
                        async for chunk in response.body_iterator:
                            if isinstance(chunk, bytes):
                                chunk = chunk.decode("utf-8")
                            # Pass through SSE data lines
                            yield chunk
                        # Send final [DONE] marker
                        yield "data: [DONE]\n\n"
                    except Exception as e:
                        log.error(
                            "Public API stream error: request_id=%s error=%s",
                            ctx.request_id,
                            str(e),
                        )

                latency_ms = int((time.monotonic() - start) * 1000)
                log.info(
                    "Public API chat stream started: request_id=%s user_id=%s model=%s latency_ms=%d",
                    ctx.request_id,
                    ctx.user_id,
                    model_id,
                    latency_ms,
                )

                return StreamingResponse(
                    public_stream_wrapper(),
                    media_type="text/event-stream",
                    headers={
                        "X-Request-ID": ctx.request_id,
                        "Cache-Control": "no-cache",
                    },
                )
            else:
                # If internal returned a dict (non-streaming fallback)
                return _format_completion_response(response, completion_id, model_id, ctx, start)

        else:
            # Non-streaming response
            response = await generate_chat_completion(
                request=request,
                form_data=internal_form,
                user=user,
                bypass_filter=True,
            )

            return _format_completion_response(response, completion_id, model_id, ctx, start)

    except HTTPException:
        raise
    except Exception as e:
        log.error(
            "Public API chat error: request_id=%s user_id=%s model=%s error=%s",
            ctx.request_id,
            ctx.user_id,
            model_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the completion.",
        )


def _format_completion_response(
    response, completion_id: str, model_id: str, ctx: PublicAPIContext, start: float
) -> dict:
    """Format internal response to OpenAI-compatible public API response."""
    latency_ms = int((time.monotonic() - start) * 1000)
    log.info(
        "Public API chat completion: request_id=%s user_id=%s model=%s latency_ms=%d",
        ctx.request_id,
        ctx.user_id,
        model_id,
        latency_ms,
    )

    if isinstance(response, dict):
        # Already OpenAI-compatible format from internal API
        choices = response.get("choices", [])
        usage = response.get("usage", {})

        formatted_choices = []
        for i, choice in enumerate(choices):
            msg = choice.get("message", {})
            formatted_choices.append(
                PublicChatCompletionChoice(
                    index=i,
                    message=PublicChatCompletionChoiceMessage(
                        role=msg.get("role", "assistant"),
                        content=msg.get("content", ""),
                    ),
                    finish_reason=choice.get("finish_reason", "stop"),
                ).model_dump()
            )

        if not formatted_choices:
            # Fallback — try to extract content from a simple response
            content = response.get("content", response.get("message", {}).get("content", ""))
            if content:
                formatted_choices = [
                    PublicChatCompletionChoice(
                        index=0,
                        message=PublicChatCompletionChoiceMessage(
                            role="assistant",
                            content=content,
                        ),
                        finish_reason="stop",
                    ).model_dump()
                ]

        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": formatted_choices,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }
    else:
        # Unexpected response type
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": str(response)},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
