"""
Internal ReAct Agent API — POST /agents/run

The ONLY endpoint where OUR backend executes tools. The model picks internal tools from
the per-run allow-list, the backend executes them, feeds observations back, and loops
until a final answer or max_steps. Thought / reasoning is never exposed — only the final
answer and a sanitized tool_trace are returned.
"""

import logging
import time

from fastapi import APIRouter, Depends, Request, status

from open_webui.routers.public.agent.react_loop import run_react
from open_webui.routers.public.agent.tool_registry import available_tool_names
from open_webui.routers.public.deps import PublicAPIContext, get_public_api_context
from open_webui.routers.public.errors import PublicAPIError
from open_webui.routers.public.rate_limit import check_rate_limit
from open_webui.routers.public.schemas import (
    PublicAgentRunRequest,
    PublicAgentRunResponse,
    PublicAgentToolTraceItem,
)
from open_webui.routers.public.tools_schema import validate_messages
from open_webui.routers.public import vllm_client
from open_webui.routers.public.model_alias import alias_candidates, to_internal_id
from open_webui.utils.models import get_all_models, get_filtered_models

log = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/agents/run",
    response_model=PublicAgentRunResponse,
    summary="Run the internal ReAct agent",
    description=(
        "Runs a server-side ReAct loop (Thought → Action → Observation → Final Answer). "
        "Internal tools are executed by OUR backend, restricted to `allowed_tools`. "
        "Reasoning is never exposed — only the final answer and a safe tool_trace are returned."
    ),
    responses={
        400: {"description": "Invalid request (unknown tool, bad messages, etc.)"},
        401: {"description": "Invalid or missing API key"},
        403: {"description": "Insufficient permissions / model not allowed"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def run_agent(
    request: Request,
    form_data: PublicAgentRunRequest,
    ctx: PublicAPIContext = Depends(get_public_api_context),
):
    await check_rate_limit(request, ctx.user_id, "agents_run", ctx.request_id)
    start = time.monotonic()

    # Validate messages
    validate_messages([m.model_dump() for m in form_data.messages], ctx.request_id)

    # Validate allowed_tools against the registry
    registry = set(available_tool_names())
    unknown = [t for t in form_data.allowed_tools if t not in registry]
    if unknown:
        raise PublicAPIError(
            status.HTTP_400_BAD_REQUEST,
            "unknown_tool",
            f"Unknown internal tool(s): {unknown}. Available: {sorted(registry)}.",
            ctx.request_id,
        )

    # Model existence + access control
    from open_webui.models.users import Users

    user = await Users.get_user_by_id(ctx.user_id)
    if user is None:
        raise PublicAPIError(status.HTTP_401_UNAUTHORIZED, "unauthorized", "User not found.", ctx.request_id)
    if not request.app.state.MODELS:
        await get_all_models(request, user=user)
    candidates = alias_candidates(form_data.model)
    if not candidates & request.app.state.MODELS.keys():
        raise PublicAPIError(
            status.HTTP_400_BAD_REQUEST, "model_not_found",
            f"Model '{form_data.model}' not found.", ctx.request_id,
        )
    filtered = await get_filtered_models(list(request.app.state.MODELS.values()), user)
    if not candidates & {m.get("id") for m in filtered}:
        raise PublicAPIError(
            status.HTTP_403_FORBIDDEN, "model_forbidden",
            f"You do not have access to model '{form_data.model}'.", ctx.request_id,
        )

    try:
        result = await run_react(
            model=to_internal_id(form_data.model),
            messages=[m.model_dump(exclude_none=True) for m in form_data.messages],
            allowed_tools=form_data.allowed_tools,
            max_steps=form_data.max_steps,
            temperature=form_data.temperature,
            max_tokens=form_data.max_tokens,
            request_id=ctx.request_id,
            enable_intent_router=form_data.enable_intent_router,
        )
    except vllm_client.VLLMError:
        raise PublicAPIError(
            status.HTTP_502_BAD_GATEWAY, "upstream_error",
            "The model server could not process the request.", ctx.request_id,
        )
    except PublicAPIError:
        raise
    except Exception as e:  # noqa: BLE001
        log.error("Agent run error: request_id=%s error=%s", ctx.request_id, str(e))
        raise PublicAPIError(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error",
            "An error occurred while running the agent.", ctx.request_id,
        )

    latency_ms = int((time.monotonic() - start) * 1000)
    log.info(
        "Public API agent done: request_id=%s model=%s steps=%d latency_ms=%d",
        ctx.request_id, form_data.model, result["steps"], latency_ms,
    )

    return PublicAgentRunResponse(
        answer=result["answer"],
        tool_trace=[PublicAgentToolTraceItem(**t) for t in result["tool_trace"]],
        steps=result["steps"],
        finish_reason=result["finish_reason"],
        intent=result.get("intent"),
    )
