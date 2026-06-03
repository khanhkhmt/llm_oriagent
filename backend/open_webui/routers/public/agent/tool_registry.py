"""
Internal tool registry for the ReAct agent (/agents/run).

These tools are executed by OUR backend (never by /chat/completions). Each entry has:
  - schema  : an OpenAI function-tool definition advertised to the model
  - handler : an async callable (args: dict) -> str  returning a safe Observation string

To add a real tool, register it here. Keep handlers side-effect-safe and never return
secrets / internal stack traces. The handler's returned string is fed back to the model
verbatim as a role="tool" observation.

# TODO: register your real internal tools here, e.g.:
#   search_docs   -> wire to open_webui retrieval/knowledge (enforce data access control)
#   read_database -> wire to a read-only, parameterized query layer
"""

import json
from datetime import datetime, timezone
from typing import Awaitable, Callable


ToolHandler = Callable[[dict], Awaitable[str]]


# ─── Example tools (safe, no side effects) ────────────────────────────────────

async def _get_time(args: dict) -> str:
    """Return current UTC time. Optional arg: tz_offset_hours (int)."""
    offset = 0
    try:
        offset = int(args.get("tz_offset_hours", 0))
    except (TypeError, ValueError):
        offset = 0
    offset = max(-14, min(14, offset))
    now = datetime.now(timezone.utc)
    return json.dumps(
        {"utc": now.isoformat(), "tz_offset_hours": offset},
        ensure_ascii=False,
    )


async def _echo(args: dict) -> str:
    """Echo back the provided text (demonstration tool)."""
    text = args.get("text", "")
    return json.dumps({"echo": str(text)[:2000]}, ensure_ascii=False)


# ─── Registry ─────────────────────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, dict] = {
    "get_time": {
        "schema": {
            "type": "function",
            "function": {
                "name": "get_time",
                "description": "Get the current UTC time, optionally offset by hours.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tz_offset_hours": {
                            "type": "integer",
                            "description": "Hours to offset from UTC (-14..14).",
                        }
                    },
                    "required": [],
                },
            },
        },
        "handler": _get_time,
    },
    "echo": {
        "schema": {
            "type": "function",
            "function": {
                "name": "echo",
                "description": "Echo back the provided text. Useful for testing the agent loop.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to echo back."}
                    },
                    "required": ["text"],
                },
            },
        },
        "handler": _echo,
    },
}


def available_tool_names() -> list[str]:
    return sorted(TOOL_REGISTRY.keys())


def get_tool_schemas(allowed_tools: list[str]) -> list[dict]:
    """Return OpenAI tool schemas for the subset of allowed tools that exist."""
    return [TOOL_REGISTRY[name]["schema"] for name in allowed_tools if name in TOOL_REGISTRY]


def get_handler(name: str) -> ToolHandler | None:
    entry = TOOL_REGISTRY.get(name)
    return entry["handler"] if entry else None


def get_tool_parameters(name: str) -> dict | None:
    """Return the JSON-Schema `parameters` object for a tool, or None."""
    entry = TOOL_REGISTRY.get(name)
    if not entry:
        return None
    return entry.get("schema", {}).get("function", {}).get("parameters")
