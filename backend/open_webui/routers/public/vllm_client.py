"""
vLLM client for the OriAgent Public API.

Talks directly to the vLLM OpenAI-compatible server (default http://127.0.0.1:8000/v1),
bypassing the internal thinking gateway so that `tools` / `tool_choice` and the
resulting `tool_calls` pass through untouched.

This client NEVER executes tools — it only relays the OpenAI-compatible request to
vLLM and returns whatever the model produced. Tool execution for third-party tools is
the caller's responsibility (external ReAct). Internal ReAct (/agents/run) executes
tools via its own tool_executor, not here.
"""

import json
import logging
import os
import re
import uuid
from typing import AsyncIterator, Optional

import aiohttp

log = logging.getLogger(__name__)


# ─── Configuration ───────────────────────────────────────────────────────────

VLLM_BASE_URL = os.environ.get("PUBLIC_VLLM_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
VLLM_API_KEY = os.environ.get("PUBLIC_VLLM_API_KEY", "")
VLLM_TIMEOUT_SECONDS = float(os.environ.get("PUBLIC_VLLM_TIMEOUT", "300"))


class VLLMError(Exception):
    """Raised when the vLLM upstream returns a non-2xx response or is unreachable."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


# ─── Reasoning suppression ───────────────────────────────────────────────────

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", flags=re.DOTALL)


def strip_reasoning(text: Optional[str]) -> Optional[str]:
    """Remove <think>...</think> blocks so chain-of-thought never leaks to clients."""
    if not text:
        return text
    cleaned = _THINK_BLOCK_RE.sub("", text)
    return cleaned.strip() if cleaned.strip() else cleaned


def _scrub_message_reasoning(message: dict) -> dict:
    """Strip reasoning from an assistant message in-place-safe manner.

    Never touches tool_calls. Drops vLLM's `reasoning_content` field entirely.
    """
    if not isinstance(message, dict):
        return message
    message.pop("reasoning_content", None)
    if message.get("content") is not None:
        message["content"] = strip_reasoning(message["content"])
    return message


# ─── Leaked tool-call recovery + finish_reason reconciliation ─────────────────
#
# Some model/parser combinations (e.g. vLLM started WITHOUT a matching
# --tool-call-parser) leak raw tool-call markup into `content` instead of
# returning structured `tool_calls`, or set finish_reason="tool_calls" while
# leaving tool_calls empty. These helpers enforce the public contract so the
# client never sees an inconsistent state.

# Matches a leaked <tool_call> ... </tool_call> block (Hermes / Qwen formats).
_TOOL_CALL_BLOCK_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
# Qwen "function-tag" form: <function=name> ... </function>
_FUNCTION_TAG_RE = re.compile(r"<function=([^>\s]+)\s*>(.*?)</function>", re.DOTALL)
_PARAMETER_TAG_RE = re.compile(r"<parameter=([^>\s]+)\s*>(.*?)</parameter>", re.DOTALL)


def _parse_one_tool_call(block: str):
    """Parse a single leaked tool-call block into (name, arguments_json_str) or None."""
    block = block.strip()

    # Hermes-style JSON form: {"name": "...", "arguments": {...}}
    try:
        obj = json.loads(block)
        if isinstance(obj, dict) and obj.get("name"):
            args = obj.get("arguments", obj.get("parameters", {}))
            if not isinstance(args, str):
                args = json.dumps(args, ensure_ascii=False)
            return str(obj["name"]), args
    except (json.JSONDecodeError, ValueError):
        pass

    # Qwen "function-tag" form.
    fm = _FUNCTION_TAG_RE.search(block)
    if fm:
        name = fm.group(1).strip()
        params = {pm.group(1).strip(): pm.group(2).strip() for pm in _PARAMETER_TAG_RE.finditer(fm.group(2))}
        return name, json.dumps(params, ensure_ascii=False)

    return None


def extract_leaked_tool_calls(content: Optional[str]):
    """Parse raw <tool_call> XML leaked into `content`.

    Returns (cleaned_content, tool_calls). `tool_calls` is [] when none are found;
    `cleaned_content` has the recovered XML removed (None if it becomes empty).
    """
    if not content or "<tool_call>" not in content:
        return content, []

    tool_calls = []
    for m in _TOOL_CALL_BLOCK_RE.finditer(content):
        parsed = _parse_one_tool_call(m.group(1))
        if parsed:
            name, args = parsed
            tool_calls.append(
                {
                    "id": f"call_{uuid.uuid4().hex[:24]}",
                    "type": "function",
                    "function": {"name": name, "arguments": args},
                }
            )

    cleaned = _TOOL_CALL_BLOCK_RE.sub("", content).strip()
    return (cleaned or None), tool_calls


def reconcile_completion(data: dict, allow_tool_calls: bool = True) -> dict:
    """Enforce the public tool-calling contract on a non-streaming vLLM response.

    Fixes the inconsistencies reproduced live against Qwen + qwen3_coder:
      1. Raw <tool_call> XML leaked into content (seen with tool_choice='none' and
         when a parser does not decode the model's markup) -> the XML is always
         stripped from content. It is promoted to structured tool_calls ONLY when
         tool calls are permitted for this request (allow_tool_calls=True).
      2. finish_reason == 'tool_calls' but tool_calls empty (seen with
         tool_choice='required'/named) -> downgraded to 'stop'.
      3. tool_calls present but finish_reason != 'tool_calls' -> set 'tool_calls'.

    With allow_tool_calls=False (chat mode / tool_choice='none') the response can
    never carry tool_calls — it only gets the leaked XML cleaned out.

    Guarantees no choice is left with finish_reason='tool_calls' AND no tool_calls.
    Mutates `data` in place and returns it.
    """
    for choice in data.get("choices", []):
        if not isinstance(choice, dict):
            continue
        msg = choice.get("message")
        if not isinstance(msg, dict):
            continue

        tool_calls = msg.get("tool_calls") or []
        content = msg.get("content")

        # 1. Recover / strip leaked XML tool calls emitted as plain text.
        if not tool_calls and content and "<tool_call>" in content:
            cleaned, recovered = extract_leaked_tool_calls(content)
            if recovered:
                msg["content"] = cleaned  # always strip the raw markup
                if allow_tool_calls:
                    tool_calls = recovered
                    msg["tool_calls"] = recovered

        # 2/3. Reconcile finish_reason with the actual presence of tool_calls.
        if tool_calls:
            choice["finish_reason"] = "tool_calls"
        elif choice.get("finish_reason") == "tool_calls":
            choice["finish_reason"] = "stop"
            msg.pop("tool_calls", None)

    return data


# ─── Streaming reasoning filter (handles <think> split across chunks) ─────────


def _partial_suffix_len(s: str, tag: str) -> int:
    """Longest k in [1, len(tag)-1] such that s endswith tag[:k] (0 if none)."""
    for k in range(min(len(s), len(tag) - 1), 0, -1):
        if s.endswith(tag[:k]):
            return k
    return 0


class _ReasoningStreamFilter:
    """Strips <think>...</think> from streamed content, even when a block spans
    multiple chunks. Holds back any text that could be the start of a tag until it
    can be resolved. Tool-call deltas are never routed through this filter.
    """

    _OPEN = "<think>"
    _CLOSE = "</think>"

    def __init__(self):
        self._buf = ""
        self._in_think = False

    def feed(self, text: str) -> str:
        self._buf += text
        out = []
        while self._buf:
            if self._in_think:
                end = self._buf.find(self._CLOSE)
                if end == -1:
                    keep = _partial_suffix_len(self._buf, self._CLOSE)
                    self._buf = self._buf[-keep:] if keep else ""
                    return "".join(out)
                self._buf = self._buf[end + len(self._CLOSE):]
                self._in_think = False
            else:
                start = self._buf.find(self._OPEN)
                if start == -1:
                    keep = _partial_suffix_len(self._buf, self._OPEN)
                    if keep:
                        out.append(self._buf[:-keep])
                        self._buf = self._buf[-keep:]
                    else:
                        out.append(self._buf)
                        self._buf = ""
                    return "".join(out)
                out.append(self._buf[:start])
                self._buf = self._buf[start + len(self._OPEN):]
                self._in_think = True
        return "".join(out)

    def flush(self) -> str:
        """Emit any trailing buffered non-think text at end of stream."""
        if self._in_think:
            self._buf = ""
            return ""
        out, self._buf = self._buf, ""
        return out


# ─── HTTP helpers ────────────────────────────────────────────────────────────

def _headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if VLLM_API_KEY:
        headers["Authorization"] = f"Bearer {VLLM_API_KEY}"
    return headers


def _timeout() -> aiohttp.ClientTimeout:
    return aiohttp.ClientTimeout(total=VLLM_TIMEOUT_SECONDS)


# ─── Public client API ───────────────────────────────────────────────────────

async def chat_completion(payload: dict, *, scrub_reasoning: bool = True) -> dict:
    """Non-streaming chat completion against vLLM.

    Args:
        payload: OpenAI-compatible request body (model, messages, tools, tool_choice, ...).
                 `stream` is forced to False here.
        scrub_reasoning: When True, strips <think> blocks / reasoning_content from the
                         returned assistant messages. Disable only for internal ReAct
                         where the loop needs to inspect raw output (it still never
                         exposes it to the client).

    Returns:
        The parsed JSON response dict from vLLM (OpenAI chat.completion shape).

    Raises:
        VLLMError on transport failure or non-2xx upstream response.
    """
    body = {**payload, "stream": False}
    url = f"{VLLM_BASE_URL}/chat/completions"

    try:
        async with aiohttp.ClientSession(timeout=_timeout(), trust_env=True) as session:
            async with session.post(url, json=body, headers=_headers()) as resp:
                text = await resp.text()
                if resp.status != 200:
                    log.warning(
                        "vLLM upstream error: status=%d body=%s", resp.status, text[:500]
                    )
                    raise VLLMError(resp.status, f"vLLM upstream returned {resp.status}")
                data = json.loads(text)
    except aiohttp.ClientError as e:
        log.error("vLLM connection error: %s", str(e))
        raise VLLMError(503, "Could not reach the model server.")

    # Enforce the tool-calling contract before anything else (recover leaked XML,
    # reconcile finish_reason). Runs for every caller, including internal ReAct.
    # Tool calls are only permitted when the request actually allows them (tools
    # present and tool_choice != 'none'); otherwise leaked XML is merely stripped.
    allow_tool_calls = bool(payload.get("tools")) and payload.get("tool_choice") != "none"
    reconcile_completion(data, allow_tool_calls=allow_tool_calls)

    if scrub_reasoning:
        for choice in data.get("choices", []):
            if isinstance(choice, dict) and isinstance(choice.get("message"), dict):
                _scrub_message_reasoning(choice["message"])

    return data


async def chat_completion_stream(payload: dict) -> AsyncIterator[bytes]:
    """Streaming chat completion against vLLM, yielding raw SSE lines (OpenAI format).

    Forwards `tool_calls` deltas verbatim. `<think>` content is suppressed best-effort
    on plain text deltas; tool_call deltas are never altered. Always terminates with a
    `data: [DONE]` marker.
    """
    body = {**payload, "stream": True}
    url = f"{VLLM_BASE_URL}/chat/completions"

    filt = _ReasoningStreamFilter()
    meta: dict = {}

    try:
        async with aiohttp.ClientSession(timeout=_timeout(), trust_env=True) as session:
            async with session.post(url, json=body, headers=_headers()) as resp:
                if resp.status != 200:
                    err_text = await resp.text()
                    log.warning(
                        "vLLM stream upstream error: status=%d body=%s",
                        resp.status,
                        err_text[:500],
                    )
                    raise VLLMError(resp.status, f"vLLM upstream returned {resp.status}")

                async for raw_line in resp.content:
                    line = raw_line.decode("utf-8", errors="ignore")
                    if not line.strip():
                        continue
                    if not line.startswith("data:"):
                        # Pass through any non-data lines unchanged
                        yield raw_line
                        continue

                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        # We emit our own [DONE] at the end; skip upstream's
                        continue

                    sanitized = _sanitize_stream_chunk(data_str, filt, meta)
                    yield f"data: {sanitized}\n\n".encode("utf-8")
    except aiohttp.ClientError as e:
        log.error("vLLM stream connection error: %s", str(e))
        raise VLLMError(503, "Could not reach the model server.")

    # Flush any non-think text the filter was still holding back at end of stream.
    tail = filt.flush()
    if tail and meta.get("id"):
        flush_chunk = {
            "id": meta["id"],
            "object": "chat.completion.chunk",
            "created": meta.get("created"),
            "model": meta.get("model"),
            "choices": [{"index": 0, "delta": {"content": tail}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(flush_chunk, ensure_ascii=False)}\n\n".encode("utf-8")

    yield b"data: [DONE]\n\n"


def _sanitize_stream_chunk(data_str: str, filt: "_ReasoningStreamFilter", meta: dict) -> str:
    """Strip reasoning from a streaming chunk's text delta, handling <think> blocks
    that span multiple chunks (via `filt`). Leaves tool_calls untouched.

    If the chunk is not valid JSON, returns it unchanged (fail-open passthrough).
    """
    try:
        obj = json.loads(data_str)
    except (json.JSONDecodeError, ValueError):
        return data_str

    # Remember chunk metadata so we can emit a trailing flush chunk if needed.
    if not meta.get("id") and obj.get("id"):
        meta["id"] = obj.get("id")
        meta["model"] = obj.get("model")
        meta["created"] = obj.get("created")

    for choice in obj.get("choices", []):
        delta = choice.get("delta") if isinstance(choice, dict) else None
        if not isinstance(delta, dict):
            continue
        # Never alter tool_calls deltas.
        delta.pop("reasoning_content", None)
        if delta.get("content"):
            delta["content"] = filt.feed(delta["content"])
    return json.dumps(obj, ensure_ascii=False)
