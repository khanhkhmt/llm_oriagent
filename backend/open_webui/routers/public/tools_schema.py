"""
Validation + request classification for OpenAI-compatible tool calling on the Public API.

These validators enforce the public contract BEFORE anything is forwarded to vLLM:
- tools must follow the OpenAI function-tool schema
- messages must use valid roles, with tool/assistant constraints
- tool_choice must be a recognized value

All failures raise PublicAPIError so the client gets the standard structured error.
"""

import json
import re
from typing import Any, Optional

from open_webui.routers.public.errors import PublicAPIError

# ─── Limits ──────────────────────────────────────────────────────────────────

MAX_TOOLS = 32
MAX_TOOL_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 4096
MAX_PARAMETERS_BYTES = 16384  # serialized JSON-schema size cap per tool

VALID_ROLES = {"system", "user", "assistant", "tool"}
TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

MODE_CHAT = "chat"
MODE_EXTERNAL_TOOL_CALLING = "external_tool_calling"
MODE_INTERNAL_REACT = "internal_react"


def _err(code: str, message: str, request_id: str = "") -> PublicAPIError:
    return PublicAPIError(
        status_code=400,
        code=code,
        message=message,
        request_id=request_id,
    )


# ─── Tools ───────────────────────────────────────────────────────────────────

def validate_tools(tools: Optional[list], request_id: str = "") -> None:
    """Validate an OpenAI-style tools array. No-op when tools is falsy."""
    if not tools:
        return

    if not isinstance(tools, list):
        raise _err("invalid_tools_schema", "`tools` must be an array.", request_id)

    if len(tools) > MAX_TOOLS:
        raise _err(
            "too_many_tools",
            f"Too many tools: {len(tools)} (max {MAX_TOOLS}).",
            request_id,
        )

    seen_names = set()
    for i, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise _err("invalid_tools_schema", f"tools[{i}] must be an object.", request_id)
        if tool.get("type") != "function":
            raise _err(
                "invalid_tools_schema",
                f"tools[{i}].type must be 'function'.",
                request_id,
            )
        fn = tool.get("function")
        if not isinstance(fn, dict):
            raise _err(
                "invalid_tools_schema",
                f"tools[{i}].function must be an object.",
                request_id,
            )

        name = fn.get("name")
        if not isinstance(name, str) or not TOOL_NAME_RE.match(name):
            raise _err(
                "invalid_tool_name",
                f"tools[{i}].function.name must match [a-zA-Z0-9_-] (1-{MAX_TOOL_NAME_LEN} chars).",
                request_id,
            )
        if name in seen_names:
            raise _err("duplicate_tool_name", f"Duplicate tool name '{name}'.", request_id)
        seen_names.add(name)

        description = fn.get("description", "")
        if description is not None and len(str(description)) > MAX_DESCRIPTION_LEN:
            raise _err(
                "tool_description_too_long",
                f"tools[{i}].function.description exceeds {MAX_DESCRIPTION_LEN} chars.",
                request_id,
            )

        parameters = fn.get("parameters")
        if parameters is not None:
            if not isinstance(parameters, dict):
                raise _err(
                    "invalid_tools_schema",
                    f"tools[{i}].function.parameters must be a JSON-Schema object.",
                    request_id,
                )
            try:
                serialized = json.dumps(parameters)
            except (TypeError, ValueError):
                raise _err(
                    "invalid_tools_schema",
                    f"tools[{i}].function.parameters is not JSON-serializable.",
                    request_id,
                )
            if len(serialized) > MAX_PARAMETERS_BYTES:
                raise _err(
                    "tool_parameters_too_large",
                    f"tools[{i}].function.parameters exceeds {MAX_PARAMETERS_BYTES} bytes.",
                    request_id,
                )


# ─── tool_choice ─────────────────────────────────────────────────────────────

def validate_tool_choice(
    tool_choice: Any, request_id: str = "", tool_names: Optional[set] = None
) -> None:
    """Validate tool_choice: 'auto'|'none'|'required' or {type:function,function:{name}}.

    When `tool_names` is provided (the set of names in `tools`), enforce that:
      - 'required' / a named choice require at least one tool to be present, and
      - a named choice references a function that actually exists in `tools`.
    Passing tool_names=None skips these cross-checks (back-compat).
    """
    if tool_choice is None:
        return
    if isinstance(tool_choice, str):
        if tool_choice not in {"auto", "none", "required"}:
            raise _err(
                "invalid_tool_choice",
                "tool_choice string must be 'auto', 'none', or 'required'.",
                request_id,
            )
        if tool_choice == "required" and tool_names is not None and not tool_names:
            raise _err(
                "invalid_tool_choice",
                "tool_choice 'required' needs at least one tool in `tools`.",
                request_id,
            )
        return
    if isinstance(tool_choice, dict):
        if tool_choice.get("type") != "function":
            raise _err("invalid_tool_choice", "tool_choice.type must be 'function'.", request_id)
        fn = tool_choice.get("function")
        if not isinstance(fn, dict) or not isinstance(fn.get("name"), str):
            raise _err(
                "invalid_tool_choice",
                "tool_choice.function.name must be a string.",
                request_id,
            )
        if tool_names is not None and fn["name"] not in tool_names:
            raise _err(
                "invalid_tool_choice",
                f"tool_choice names function '{fn['name']}', which is not in `tools`.",
                request_id,
            )
        return
    raise _err("invalid_tool_choice", "tool_choice has an invalid type.", request_id)


# ─── Messages ────────────────────────────────────────────────────────────────

def validate_messages(messages: list, request_id: str = "") -> None:
    """Validate roles and tool/assistant message constraints."""
    if not messages:
        raise _err("invalid_messages", "messages must contain at least one item.", request_id)

    for i, msg in enumerate(messages):
        # msg may be a pydantic model dumped to dict by the caller
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
        if role not in VALID_ROLES:
            raise _err(
                "invalid_message_role",
                f"messages[{i}].role must be one of {sorted(VALID_ROLES)}.",
                request_id,
            )

        if role == "tool":
            tool_call_id = (
                msg.get("tool_call_id") if isinstance(msg, dict) else getattr(msg, "tool_call_id", None)
            )
            if not tool_call_id:
                raise _err(
                    "missing_tool_call_id",
                    f"messages[{i}] has role 'tool' but no tool_call_id.",
                    request_id,
                )

        if role == "assistant":
            tool_calls = (
                msg.get("tool_calls") if isinstance(msg, dict) else getattr(msg, "tool_calls", None)
            )
            if tool_calls:
                if not isinstance(tool_calls, list):
                    raise _err(
                        "invalid_tool_calls",
                        f"messages[{i}].tool_calls must be an array.",
                        request_id,
                    )
                for j, tc in enumerate(tool_calls):
                    tc = tc if isinstance(tc, dict) else tc.model_dump()
                    fn = tc.get("function") or {}
                    if not tc.get("id") or tc.get("type") != "function":
                        raise _err(
                            "invalid_tool_calls",
                            f"messages[{i}].tool_calls[{j}] must have id and type 'function'.",
                            request_id,
                        )
                    if not fn.get("name") or fn.get("arguments") is None:
                        raise _err(
                            "invalid_tool_calls",
                            f"messages[{i}].tool_calls[{j}].function needs name and arguments.",
                            request_id,
                        )


# ─── Request classification ──────────────────────────────────────────────────

def classify_request(
    mode: Optional[str],
    tools: Optional[list],
    tool_choice: Any,
    messages: list,
) -> str:
    """Classify a /chat/completions request into 'chat' or 'external_tool_calling'.

    Mirrors the spec's classification logic:
      - explicit mode wins
      - non-empty tools -> external_tool_calling
      - tool_choice != 'none' -> external_tool_calling
      - any message with role 'tool' -> external_tool_calling
      - otherwise -> chat
    """
    if mode:
        return mode

    if tools:
        return MODE_EXTERNAL_TOOL_CALLING

    if tool_choice is not None and tool_choice != "none":
        return MODE_EXTERNAL_TOOL_CALLING

    for msg in messages:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
        if role == "tool":
            return MODE_EXTERNAL_TOOL_CALLING

    return MODE_CHAT
