# Agents API

`POST /api/public/v1/agents/run` — runs a **server-side ReAct loop** (Thought → Action → Observation → Final Answer). Unlike `/chat/completions`, here **OriAgent executes the tools** — but only **internal** tools, restricted to the `allowed_tools` list you provide per run. The model's reasoning (Thought) is never exposed.

Use this when you want OriAgent to orchestrate the loop for you. Use [`/chat/completions`](./chat-completions.md) with `tools` when you manage the loop yourself.

## How It Works

```
Client → POST /agents/run (model, messages, allowed_tools)

  loop (up to max_steps):
    OriAgent → vLLM  [with internal tool schemas]
    if model returns tool_calls:
      OriAgent executes the internal tool → Observation
      Observation fed back to vLLM
    else:
      final answer → stop

Client ← { answer, tool_trace, steps, finish_reason }
       [no Thought / reasoning exposed]
```

## POST /agents/run

```
POST https://llm.oriagent.com/api/public/v1/agents/run
Content-Type: application/json
Authorization: Bearer sk-xxxxxxxxxxxxx
```

### Request

```json
{
  "mode": "internal_react",
  "model": "Qwen/Qwen3.5-2B",
  "messages": [
    {"role": "user", "content": "What time is it in UTC?"}
  ],
  "allowed_tools": ["get_time"],
  "temperature": 0.7,
  "max_steps": 5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model ID from `/models` |
| `messages` | array | Yes | Conversation (usually a single user message) |
| `allowed_tools` | string[] | Yes | Names of internal tools the agent may use this run |
| `max_steps` | integer | No | Max ReAct iterations, 1–8 (default `5`) |
| `temperature` | float | No | Sampling temperature 0.0–2.0 |
| `max_tokens` | integer | No | Max tokens per model call, 1–128000 |
| `enable_intent_router` | boolean | No | Route the request before the loop (default `true`). See below. |

> `allowed_tools` must contain only registered internal tool names. Unknown names return `400 unknown_tool`.

### Intent routing (`enable_intent_router`, default `true`)

Before the loop runs, a deterministic, fail-safe pre-pass classifies the request and adjusts behavior so the agent does not call data tools for general-knowledge questions or answer policy questions without looking them up:

| Category | Effect |
|----------|--------|
| `general_qa` | Tools are **not** advertised — the model answers directly (e.g. *"Bộ Y tế thành lập năm nào?"* won't trigger a data tool). |
| `data_query` | Data tools enabled; the model is told to use diacritic-free slugs that match the tool schema. |
| `policy_query` | The model is instructed to look up knowledge (e.g. `search_knowledge`) before answering — no guessing regulations. |
| `mixed` | Both data and knowledge lookup are encouraged. |
| `tool_task` | Default — tools enabled, model decides. |

The router is conservative: it only suppresses tools for confident general-knowledge questions, so a misclassification can at most cause an unnecessary tool call, never a missing one. Set `enable_intent_router: false` to disable it entirely. The detected category is returned in `intent` (see below).

> **Argument hardening:** before a tool runs, the agent coerces arguments to the tool's JSON Schema and normalizes accented/cased keys — e.g. the model's `{"năm": "2023"}` becomes `{"nam": 2023}`. It also follows strict grounding rules: facts/numbers/names must come from tool observations, never invented.

### Response

```json
{
  "answer": "The current UTC time is 2026-06-01T10:30:00+00:00.",
  "tool_trace": [
    {
      "tool_name": "get_time",
      "arguments": {},
      "status": "success"
    }
  ],
  "steps": 2,
  "finish_reason": "stop",
  "intent": "general_qa"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Final answer only — no reasoning or Thought exposed |
| `tool_trace` | array | Safe record of internal tool executions |
| `tool_trace[].tool_name` | string | Tool that was called |
| `tool_trace[].arguments` | object | Parsed arguments passed to the tool (after schema coercion / slug normalization) |
| `tool_trace[].status` | string | `"success"` or `"error"` |
| `steps` | integer | Number of ReAct iterations performed |
| `finish_reason` | string | `"stop"` (model finished) or `"max_steps"` (bounded out) |
| `intent` | string | Detected category: `general_qa` \| `data_query` \| `policy_query` \| `mixed` \| `tool_task` |

> When `finish_reason` is `"max_steps"`, a final answer is still synthesized from the last model response.

---

## Available Internal Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_time` | Current UTC time | `tz_offset_hours` (integer, optional, −14..14) |
| `echo` | Echoes back provided text — useful for testing | `text` (string, required) |

### Adding Your Own Tools

Register new tools in [backend/open_webui/routers/public/agent/tool_registry.py](../../backend/open_webui/routers/public/agent/tool_registry.py). Each entry needs:

1. An OpenAI function schema advertised to the model
2. An `async` handler `(args: dict) -> str` that returns a safe observation string

Keep handlers side-effect-safe and never return secrets or stack traces — the observation string is fed back to the model verbatim.

---

## Examples

### curl
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/agents/run" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.5-2B",
    "messages": [{"role": "user", "content": "What time is it in UTC?"}],
    "allowed_tools": ["get_time"],
    "max_steps": 4
  }'
```

### Python
```python
import requests

resp = requests.post(
    "https://llm.oriagent.com/api/public/v1/agents/run",
    headers={"Authorization": "Bearer sk-xxxxxxxxxxxxx"},
    json={
        "model": "Qwen/Qwen3.5-2B",
        "messages": [{"role": "user", "content": "What time is it in UTC?"}],
        "allowed_tools": ["get_time"],
        "max_steps": 4,
    },
)
data = resp.json()
print(data["answer"])
print("Steps:", data["steps"])
for trace in data["tool_trace"]:
    print(f"  {trace['tool_name']}({trace['arguments']}) → {trace['status']}")
```

### JavaScript
```javascript
const resp = await fetch("https://llm.oriagent.com/api/public/v1/agents/run", {
  method: "POST",
  headers: {
    "Authorization": "Bearer sk-xxxxxxxxxxxxx",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "Qwen/Qwen3.5-2B",
    messages: [{ role: "user", content: "What time is it in UTC?" }],
    allowed_tools: ["get_time"],
    max_steps: 4,
  }),
});
const { answer, tool_trace, steps } = await resp.json();
console.log(answer);
```

---

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | `unknown_tool` | `allowed_tools` contains an unregistered tool name |
| 400 | `model_not_found` | Model ID does not exist |
| 400 | `invalid_message_role` | Invalid message role |
| 401 | `unauthorized` | Invalid or missing API key |
| 403 | `model_forbidden` | Model not permitted for this API key |
| 429 | `rate_limit_error` | Rate limit exceeded (20 req/min) |
| 502 | `upstream_error` | The vLLM model server failed |

See [errors.md](./errors.md) for the full error format.
