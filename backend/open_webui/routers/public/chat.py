"""
Public Chat Completion API — POST /chat/completions

OpenAI-compatible chat completion for third-party integrations, served directly by
the vLLM OpenAI-compatible server (bypassing the internal thinking gateway so that
tools / tool_choice / tool_calls pass through untouched).

Two modes (auto-classified when `mode` is omitted):
  - "chat"                  : plain completion. tools are ignored, tool_choice forced to "none".
  - "external_tool_calling" : the model MAY emit tool_calls. The CLIENT executes them and
                              sends observations back as role="tool" messages.

This endpoint NEVER executes third-party tools. Internal tool execution only happens in
POST /agents/run.
"""

import logging
import time
import uuid

from fastapi import APIRouter, Depends, Request, status
from starlette.responses import StreamingResponse

from open_webui.routers.public import grounding
from open_webui.routers.public.deps import PublicAPIContext, get_public_api_context
from open_webui.routers.public.errors import PublicAPIError
from open_webui.routers.public.rate_limit import check_rate_limit
from open_webui.routers.public.schemas import PublicChatCompletionRequest
from open_webui.routers.public.tools_schema import (
    MODE_CHAT,
    MODE_EXTERNAL_TOOL_CALLING,
    classify_request,
    validate_messages,
    validate_tool_choice,
    validate_tools,
)
from open_webui.routers.public import vllm_client
from open_webui.routers.public.model_alias import IDENTITY_PROMPT, alias_candidates, to_internal_id
from open_webui.utils.models import get_all_models, get_filtered_models

log = logging.getLogger(__name__)

router = APIRouter()


async def _resolve_model_or_403(request: Request, ctx: PublicAPIContext, model_id: str) -> str:
    """Validate the model exists and the API-key user is allowed to use it.
    Returns the resolved internal model ID.
    """
    from open_webui.models.users import Users

    user = await Users.get_user_by_id(ctx.user_id)
    if user is None:
        raise PublicAPIError(status.HTTP_401_UNAUTHORIZED, "unauthorized", "User not found.", ctx.request_id)

    if not request.app.state.MODELS:
        await get_all_models(request, user=user)

    # The registry may know the model under its display or internal name;
    # accept whichever the client sent and check every alias.
    candidates = alias_candidates(model_id)

    if not candidates & request.app.state.MODELS.keys():
        raise PublicAPIError(
            status.HTTP_400_BAD_REQUEST, "model_not_found", f"Model '{model_id}' not found.", ctx.request_id
        )

    all_models = list(request.app.state.MODELS.values())
    filtered = await get_filtered_models(all_models, user)
    allowed_ids = {m.get("id") for m in filtered}
    if not candidates & allowed_ids:
        raise PublicAPIError(
            status.HTTP_403_FORBIDDEN,
            "model_forbidden",
            f"You do not have access to model '{model_id}'.",
            ctx.request_id,
        )
    return to_internal_id(model_id)


def _build_payload(form_data: PublicChatCompletionRequest, mode: str) -> dict:
    """Build the OpenAI-compatible payload sent to vLLM."""
    resolved_model = to_internal_id(form_data.model)

    client_messages = [msg.model_dump(exclude_none=True) for msg in form_data.messages]

    # Qwen's chat template accepts a single system message and only at the start:
    # brand identity comes first, then any leading client system messages are
    # merged into that same message.
    system_parts = [IDENTITY_PROMPT]
    while client_messages and client_messages[0].get("role") == "system":
        content = client_messages.pop(0).get("content")
        if content:
            system_parts.append(content)
    messages = [{"role": "system", "content": "\n\n".join(system_parts)}] + client_messages

    payload = {
        "model": resolved_model,
        "messages": messages,
    }

    if form_data.temperature is not None:
        payload["temperature"] = form_data.temperature
    if form_data.max_tokens is not None:
        payload["max_tokens"] = form_data.max_tokens
    if form_data.top_p is not None:
        payload["top_p"] = form_data.top_p
    if form_data.frequency_penalty is not None:
        payload["frequency_penalty"] = form_data.frequency_penalty
    if form_data.presence_penalty is not None:
        payload["presence_penalty"] = form_data.presence_penalty
    if form_data.stop is not None:
        payload["stop"] = form_data.stop
    if form_data.response_format is not None:
        # Structured output / guided decoding — forwarded verbatim to vLLM.
        payload["response_format"] = form_data.response_format

    if mode == MODE_EXTERNAL_TOOL_CALLING:
        if form_data.tools:
            payload["tools"] = [t.model_dump(exclude_none=True) for t in form_data.tools]
        # tool_choice may be a string or a named-tool object
        if form_data.tool_choice is not None:
            tc = form_data.tool_choice
            payload["tool_choice"] = tc if isinstance(tc, str) else tc.model_dump(exclude_none=True)
        elif form_data.tools:
            payload["tool_choice"] = "auto"
    else:
        # chat mode: never send tools; explicitly disable tool calling
        payload["tool_choice"] = "none"

    return payload


@router.post(
    "/chat/completions",
    summary="Create a chat completion",
    description=(
        "OpenAI-compatible chat completion. Supports plain chat and external tool calling "
        "(the model emits tool_calls for the client to execute). Streaming via SSE is supported. "
        "This endpoint never executes third-party tools."
    ),
    responses={
        400: {"description": "Invalid request (bad model, tools schema, messages, etc.)"},
        401: {"description": "Invalid or missing API key"},
        403: {"description": "Insufficient permissions / model not allowed"},
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

    # 1) Classify
    mode = classify_request(
        form_data.mode, form_data.tools, form_data.tool_choice, form_data.messages
    )

    # 2) Validate messages always; tools/tool_choice only when tool calling
    validate_messages([m.model_dump() for m in form_data.messages], ctx.request_id)
    if mode == MODE_EXTERNAL_TOOL_CALLING:
        validate_tools([t.model_dump() for t in form_data.tools] if form_data.tools else None, ctx.request_id)
        tool_names = {t.function.name for t in form_data.tools} if form_data.tools else set()
        validate_tool_choice(
            form_data.tool_choice if isinstance(form_data.tool_choice, str)
            else (form_data.tool_choice.model_dump() if form_data.tool_choice else None),
            ctx.request_id,
            tool_names=tool_names,
        )

    # 3) Model existence + access control (kept at the public edge)
    await _resolve_model_or_403(request, ctx, form_data.model)

    # 4) Build payload and call vLLM directly
    payload = _build_payload(form_data, mode)
    completion_id = f"chatcmpl_{uuid.uuid4().hex[:12]}"
    resolved_model = payload.get("model", form_data.model)

    log.info(
        "Public API chat: request_id=%s user_id=%s requested_model='%s' -> internal_model='%s' mode=%s stream=%s",
        ctx.request_id, ctx.user_id, form_data.model, resolved_model, mode, form_data.stream,
    )

    try:
        if form_data.stream:
            async def sse():
                try:
                    async for chunk in vllm_client.chat_completion_stream(payload):
                        yield chunk
                except vllm_client.VLLMError as e:
                    log.warning("Public API stream vLLM error: request_id=%s %s", ctx.request_id, e.message)

            return StreamingResponse(
                sse(),
                media_type="text/event-stream",
                headers={"X-Request-ID": ctx.request_id, "Cache-Control": "no-cache"},
            )

        data = await vllm_client.chat_completion(payload)
        data = await _apply_grounding_guard(form_data, payload, data, ctx)
        return _format_completion_response(data, completion_id, form_data.model, ctx, start)

    except vllm_client.VLLMError as e:
        raise PublicAPIError(
            status_code=502 if e.status_code not in (503,) else 503,
            code="upstream_error",
            message="The model server could not process the request.",
            request_id=ctx.request_id,
        )
    except PublicAPIError:
        raise
    except Exception as e:  # noqa: BLE001
        log.error("Public API chat error: request_id=%s error=%s", ctx.request_id, str(e))
        raise PublicAPIError(
            status_code=500, code="internal_error",
            message="An error occurred while generating the completion.",
            request_id=ctx.request_id,
        )


_GROUNDING_NUDGE = (
    "QUAN TRỌNG: Chỉ sử dụng số liệu và dữ kiện xuất hiện trong các kết quả tool phía trên. "
    "Không thêm bất kỳ con số hay khẳng định nào ngoài dữ liệu đó; nếu thiếu dữ liệu, hãy nói rõ. "
    "Trả lời cùng ngôn ngữ với người dùng và chỉ dùng ký tự Việt/Anh (không dùng ký tự ngôn ngữ khác)."
)


def _answer_and_corpus(form_data: PublicChatCompletionRequest, data: dict):
    """Extract the final answer text + the grounding corpus (tool + user content).

    Returns (answer, corpus, has_tool_msgs) or (None, ...) when the choice is a
    tool-call turn (no prose answer to check).
    """
    choices = data.get("choices") or []
    if not choices:
        return None, "", False
    msg = choices[0].get("message") or {}
    if msg.get("tool_calls"):
        return None, "", False
    answer = msg.get("content") or ""

    tool_texts, user_texts, has_tool = [], [], False
    for m in form_data.messages:
        if m.role == "tool":
            has_tool = True
            if m.content:
                tool_texts.append(m.content)
        elif m.role == "user" and m.content:
            user_texts.append(m.content)
    corpus = grounding.build_corpus(tool_texts + user_texts)
    return answer, corpus, has_tool


async def _apply_grounding_guard(
    form_data: PublicChatCompletionRequest, payload: dict, data: dict, ctx
) -> dict:
    """Detect ungrounded numbers / foreign-script in the answer; log, and (when
    enforce_grounding) run ONE corrective regeneration grounded in existing context.
    """
    answer, corpus, has_tool = _answer_and_corpus(form_data, data)
    if answer is None:
        return data  # tool-call turn — nothing to ground

    foreign = grounding.contains_foreign_script(answer)
    # Only number-check answers that are supposed to be grounded in tool data.
    ungrounded = grounding.find_ungrounded_numbers(answer, corpus) if has_tool else []

    if not ungrounded and not foreign:
        return data

    log.warning(
        "Public API grounding flag: request_id=%s ungrounded_numbers=%s foreign_script=%s enforce=%s",
        ctx.request_id, ungrounded, foreign, form_data.enforce_grounding,
    )

    if not form_data.enforce_grounding:
        return data

    # One corrective pass: force a textual answer grounded in the existing context.
    corrective = dict(payload)
    corrective.pop("tools", None)
    corrective["tool_choice"] = "none"
    corrective["temperature"] = 0
    corrective["messages"] = list(payload.get("messages", [])) + [
        {"role": "system", "content": _GROUNDING_NUDGE}
    ]
    try:
        regen = await vllm_client.chat_completion(corrective)
        new_answer, _, _ = _answer_and_corpus(form_data, regen)
        new_report = grounding.grounding_report(new_answer or "", corpus)
        log.info(
            "Public API grounding regenerated: request_id=%s now_ok=%s ungrounded=%s",
            ctx.request_id, new_report["ok"], new_report["ungrounded_numbers"],
        )
        return regen
    except vllm_client.VLLMError:
        log.warning("Public API grounding regen failed: request_id=%s (keeping original)", ctx.request_id)
        return data


def _format_completion_response(data: dict, completion_id: str, model_id: str, ctx, start) -> dict:
    """Map vLLM's chat.completion into the public response, PRESERVING tool_calls."""
    latency_ms = int((time.monotonic() - start) * 1000)
    log.info(
        "Public API chat done: request_id=%s model=%s latency_ms=%d",
        ctx.request_id, model_id, latency_ms,
    )

    usage = data.get("usage", {}) or {}
    out_choices = []
    for i, choice in enumerate(data.get("choices", [])):
        msg = choice.get("message", {}) or {}
        message_out = {
            "role": msg.get("role", "assistant"),
            "content": msg.get("content"),
        }
        if msg.get("tool_calls"):
            message_out["tool_calls"] = msg["tool_calls"]
        out_choices.append({
            "index": i,
            "message": message_out,
            "finish_reason": choice.get("finish_reason", "stop"),
        })

    return {
        "id": data.get("id", completion_id),
        "object": "chat.completion",
        "created": data.get("created", int(time.time())),
        "model": model_id,
        "choices": out_choices,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    }
