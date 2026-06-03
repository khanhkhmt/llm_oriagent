"""
Internal tool executor for the ReAct agent.

Executes a single tool call requested by the model, enforcing the per-run allow-list.
Returns (observation_string, status) where status is "success" or "error". Never leaks
stack traces — errors are returned as a safe, model-readable observation.
"""

import json
import logging
import unicodedata

from open_webui.routers.public.agent.tool_registry import get_handler, get_tool_parameters

log = logging.getLogger(__name__)


def parse_arguments(raw_arguments) -> dict:
    """Parse the model-provided arguments (usually a JSON string) into a dict."""
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if not raw_arguments:
        return {}
    try:
        parsed = json.loads(raw_arguments)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except (json.JSONDecodeError, ValueError, TypeError):
        return {}


def _strip_diacritics(s: str) -> str:
    """Lowercased, accent-stripped form ('năm' -> 'nam') for fuzzy key matching."""
    nfkd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn").lower()


def _coerce_value(value, json_type):
    """Coerce a string value to the JSON-Schema type the tool expects."""
    if not isinstance(value, str):
        return value
    v = value.strip()
    if json_type == "integer":
        try:
            return int(v)
        except ValueError:
            return value
    if json_type == "number":
        try:
            return float(v)
        except ValueError:
            return value
    if json_type == "boolean":
        low = v.lower()
        if low in {"true", "1", "yes"}:
            return True
        if low in {"false", "0", "no"}:
            return False
    return value


def coerce_arguments(args: dict, parameters_schema: dict | None) -> dict:
    """Align model-produced arguments with the tool's JSON-Schema.

    - Remaps accented/cased keys to the canonical schema property
      (e.g. the model's "năm" -> the schema's "nam").
    - Coerces string values to the declared type ("2023" -> 2023 for integer).
    Unknown keys with no schema match are passed through untouched.
    """
    if not isinstance(args, dict) or not isinstance(parameters_schema, dict):
        return args
    props = parameters_schema.get("properties")
    if not isinstance(props, dict) or not props:
        return args

    norm_to_canon = {_strip_diacritics(p): p for p in props}

    out = {}
    for key, value in args.items():
        canon = key
        if key not in props:
            match = norm_to_canon.get(_strip_diacritics(key))
            if match:
                canon = match
        spec = props.get(canon) or {}
        out[canon] = _coerce_value(value, spec.get("type"))
    return out


async def execute_tool(
    tool_name: str,
    raw_arguments,
    allowed_tools: list[str],
    request_id: str = "",
) -> tuple[str, str, dict]:
    """Execute one internal tool call.

    Returns (observation, status, parsed_args).
      - status "error" with a safe observation if the tool is not allowed / unknown / fails.
    """
    args = parse_arguments(raw_arguments)

    if tool_name not in allowed_tools:
        return (
            json.dumps({"error": f"Tool '{tool_name}' is not permitted for this run."}, ensure_ascii=False),
            "error",
            args,
        )

    handler = get_handler(tool_name)
    if handler is None:
        return (
            json.dumps({"error": f"Tool '{tool_name}' is not registered."}, ensure_ascii=False),
            "error",
            args,
        )

    # Normalize keys (accents/case) and coerce value types to the tool's schema
    # before execution, so e.g. {"năm": "2023"} becomes {"nam": 2023}.
    args = coerce_arguments(args, get_tool_parameters(tool_name))

    try:
        observation = await handler(args)
        if not isinstance(observation, str):
            observation = json.dumps(observation, ensure_ascii=False)
        return observation, "success", args
    except Exception as e:  # noqa: BLE001
        log.error(
            "Internal tool execution failed: request_id=%s tool=%s error=%s",
            request_id, tool_name, str(e),
        )
        return (
            json.dumps({"error": "Tool execution failed."}, ensure_ascii=False),
            "error",
            args,
        )
