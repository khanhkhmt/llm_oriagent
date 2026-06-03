"""
Internal ReAct loop for /agents/run.

Thought → Action → Observation → Final Answer, driven by vLLM tool calling:
  1. Call vLLM with the allowed internal tool schemas.
  2. If the model returns tool_calls, execute each via tool_executor, append the
     observations as role="tool" messages, and loop.
  3. If the model returns a normal message (no tool_calls), that is the final answer.
  4. Stop at max_steps regardless.

The loop NEVER exposes Thought / reasoning to the caller. Only the final answer and a
sanitized tool_trace are returned.
"""

import logging

from open_webui.routers.public.agent.intent_router import route_intent
from open_webui.routers.public.agent.tool_executor import execute_tool
from open_webui.routers.public.agent.tool_registry import get_tool_schemas
from open_webui.routers.public import vllm_client

log = logging.getLogger(__name__)

_AGENT_SYSTEM_PROMPT = (
    "You are an autonomous assistant. Use the provided tools when they help answer the "
    "user's request. When you have enough information, reply with a final answer in plain "
    "text and do not call any more tools. Do not reveal your internal reasoning.\n"
    "Grounding rules:\n"
    "- Base every fact, number, and name ONLY on the tool observations returned in this "
    "conversation. Never invent or guess values that are not present in an observation.\n"
    "- Do not mix data across different tool results; attribute each value to the result it "
    "came from.\n"
    "- If the observations do not contain enough information to answer, say so explicitly "
    "instead of fabricating an answer.\n"
    "- For questions about general knowledge that need no internal data, answer directly "
    "without calling any tool."
)


async def run_react(
    *,
    model: str,
    messages: list[dict],
    allowed_tools: list[str],
    max_steps: int = 5,
    temperature=None,
    max_tokens=None,
    request_id: str = "",
    enable_intent_router: bool = True,
) -> dict:
    """Run the internal ReAct loop. Returns {answer, tool_trace, steps, finish_reason, intent}."""
    tool_schemas = get_tool_schemas(allowed_tools)

    # Seed conversation with a system prompt (prepended once).
    convo: list[dict] = []
    if not messages or messages[0].get("role") != "system":
        convo.append({"role": "system", "content": _AGENT_SYSTEM_PROMPT})
    convo.extend(messages)

    # Intent routing: inject category guidance into the system prompt and decide
    # whether tools should be advertised at all (general-knowledge -> no tools).
    intent = "tool_task"
    tools_enabled = bool(tool_schemas)
    if enable_intent_router:
        route = route_intent(messages, allowed_tools)
        intent = route["category"]
        for m in convo:
            if m.get("role") == "system":
                m["content"] = f"{m.get('content', '')}\n\n{route['guidance']}".strip()
                break
        if route["suggested_tool_choice"] == "none":
            tools_enabled = False
        log.info(
            "Agent intent route: request_id=%s category=%s reason=%s tools_enabled=%s",
            request_id, intent, route["reason"], tools_enabled,
        )

    tool_trace: list[dict] = []
    answer = ""
    finish_reason = "stop"
    steps = 0

    for step in range(max_steps):
        steps = step + 1
        payload = {
            "model": model,
            "messages": convo,
        }
        if tool_schemas and tools_enabled:
            payload["tools"] = tool_schemas
            payload["tool_choice"] = "auto"
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        # scrub_reasoning=False: the loop may need raw content internally, but we never
        # return it to the client — only `answer` (final) is surfaced.
        data = await vllm_client.chat_completion(payload, scrub_reasoning=False)

        choices = data.get("choices", [])
        if not choices:
            answer = ""
            break

        message = choices[0].get("message", {}) or {}
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            # Final answer — strip any reasoning before exposing.
            answer = vllm_client.strip_reasoning(message.get("content") or "") or ""
            finish_reason = "stop"
            break

        # Append the assistant's tool-call message, then execute each tool.
        convo.append(
            {
                "role": "assistant",
                "content": message.get("content"),
                "tool_calls": tool_calls,
            }
        )

        for tc in tool_calls:
            fn = tc.get("function", {}) or {}
            name = fn.get("name", "")
            observation, status, parsed_args = await execute_tool(
                name, fn.get("arguments"), allowed_tools, request_id
            )
            tool_trace.append(
                {"tool_name": name, "arguments": parsed_args, "status": status}
            )
            convo.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "name": name,
                    "content": observation,
                }
            )
    else:
        # Loop exhausted without a final answer — make one more call WITHOUT tools to
        # force a textual answer from whatever has been gathered.
        finish_reason = "max_steps"
        try:
            forced = await vllm_client.chat_completion(
                {"model": model, "messages": convo, "tool_choice": "none"},
                scrub_reasoning=True,
            )
            fchoices = forced.get("choices", [])
            if fchoices:
                answer = (fchoices[0].get("message", {}) or {}).get("content") or ""
        except vllm_client.VLLMError:
            answer = answer or ""

    log.info(
        "Agent run: request_id=%s model=%s steps=%d tools_used=%d finish=%s intent=%s",
        request_id, model, steps, len(tool_trace), finish_reason, intent,
    )

    return {
        "answer": answer,
        "tool_trace": tool_trace,
        "steps": steps,
        "finish_reason": finish_reason,
        "intent": intent,
    }
