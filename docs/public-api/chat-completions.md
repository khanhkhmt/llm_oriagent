# Chat Completions API

`POST /api/public/v1/chat/completions` — OpenAI-compatible chat completion. Supports plain chat and **external tool calling** (the model emits `tool_calls` for your client to execute). Streaming via SSE. **This endpoint never executes your tools.**

## Request

```
POST https://llm.oriagent.com/api/public/v1/chat/completions
Content-Type: application/json
Authorization: Bearer sk-xxxxxxxxxxxxx
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model ID from `/models` |
| `messages` | array | Yes | Conversation messages (min 1) |
| `mode` | string | No | `"chat"` or `"external_tool_calling"` — auto-inferred if omitted |
| `tools` | array | No | OpenAI function tools (max 32) |
| `tool_choice` | string \| object | No | `"auto"` \| `"none"` \| `"required"` \| `{type:"function", function:{name}}` |
| `stream` | boolean | No | Stream response via SSE (default `false`) |
| `temperature` | float | No | Sampling temperature 0.0–2.0 |
| `max_tokens` | integer | No | Max tokens to generate (1–128000) |
| `top_p` | float | No | Top-p sampling 0.0–1.0 |
| `frequency_penalty` | float | No | Frequency penalty −2.0–2.0 |
| `presence_penalty` | float | No | Presence penalty −2.0–2.0 |
| `stop` | string[] | No | Stop sequences |

### Mode Inference

When `mode` is omitted the server infers it:

1. Non-empty `tools` → `external_tool_calling`
2. `tool_choice` ≠ `"none"` → `external_tool_calling`
3. Any `role:"tool"` message in the conversation → `external_tool_calling`
4. Otherwise → `chat`

In `chat` mode, `tools` are ignored and `tool_choice` is forced to `"none"`.

---

## Plain Chat

Send messages and receive a text response.

### Request
```json
{
  "model": "Qwen/Qwen3.5-2B",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "temperature": 0.7,
  "max_tokens": 512
}
```

### Response
```json
{
  "id": "chatcmpl_abc123",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "Qwen/Qwen3.5-2B",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 24,
    "completion_tokens": 9,
    "total_tokens": 33
  }
}
```

> The model's `<think>…</think>` reasoning is stripped and never returned.

---

## Tool Calling

Define function tools. When the model decides to call one, it returns `tool_calls` with `content: null` and `finish_reason: "tool_calls"`. Your client executes the tool and sends the result back.

### Tool Format

```json
{
  "type": "function",
  "function": {
    "name": "get_order",
    "description": "Fetch order details by order ID.",
    "parameters": {
      "type": "object",
      "properties": {
        "order_id": {
          "type": "string",
          "description": "The order identifier."
        }
      },
      "required": ["order_id"]
    }
  }
}
```

**Tool constraints:**
- Max 32 tools per request
- `function.name` must match `[a-zA-Z0-9_-]{1,64}`
- `parameters` must be a valid JSON Schema object (≤ 16 KB serialized)
- `description` max 4096 characters
- A named `tool_choice` (`{type:"function", function:{name}}`) must reference a function that is present in `tools`, and `"required"` / a named choice require at least one tool — otherwise `400 invalid_tool_choice`.

### `tool_choice` behavior & guarantees

The gateway normalizes the model server's output so your client always receives a consistent response:

| `tool_choice` | Behavior | Recommendation |
|---------------|----------|----------------|
| `"auto"` | The model decides. Reliable on the current model. | **Preferred** for tool calling. |
| `"none"` | Tools are never invoked. Any tool-call markup the model emits is stripped from `content` and is **not** returned as `tool_calls`. | Use for plain chat. |
| `"required"` | Forces a tool call. On the current model this may yield **no** tool call; when that happens the gateway returns `finish_reason: "stop"` (never an inconsistent `"tool_calls"` with empty `tool_calls`). | Prefer `"auto"` until the backend model fully supports it. |
| `{function:{name}}` | Requests a specific function. Same caveat as `"required"`. | Prefer `"auto"`. |

Guarantees regardless of mode:
- **`finish_reason` is always consistent with `tool_calls`** — you will never get `finish_reason: "tool_calls"` with an empty/missing `tool_calls`.
- **Raw tool-call markup never leaks into `content`** (no `<tool_call>…</tool_call>` text). When the model emits it, it is parsed into structured `tool_calls` (when tool calling is allowed) or stripped (when it is not).
- **Reasoning (`<think>…</think>`) is never returned**, including across streaming chunk boundaries.

### Output-quality controls (optional)

For weaker models, two optional request fields help keep answers grounded:

| Field | Type | Description |
|-------|------|-------------|
| `response_format` | object | OpenAI-compatible structured output forwarded to the model server for guided decoding, e.g. `{"type":"json_object"}` or `{"type":"json_schema","json_schema":{…}}`. Constrains the model to a fixed shape — recommended for analytic/numeric answers. |
| `enforce_grounding` | boolean | Default `false`. For **non-streaming** answers, the gateway checks the reply for numbers absent from the tool observations / user input and for foreign-script leakage (e.g. CJK). If found, it runs **one** corrective regeneration grounded only in the existing context. Combine with a system prompt that tells the model to report units exactly and only use numbers from tool results. |

> These are heuristics, not hard guarantees — pair them with a strict system prompt for best results.

---

## External ReAct Flow

When you manage the loop yourself:

```
Your client → POST /chat/completions (tools, tool_choice:"auto")
  ← response: assistant.tool_calls          [model wants a tool]
You execute the tool
  → POST /chat/completions (messages + assistant.tool_calls + role:"tool" observation)
  ← response: assistant.content             [final answer]
```

### Round 1 — Request
```json
{
  "model": "Qwen/Qwen3.5-2B",
  "messages": [
    {"role": "user", "content": "Check order ORD-123 for me."}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_order",
        "parameters": {
          "type": "object",
          "properties": {"order_id": {"type": "string"}},
          "required": ["order_id"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

### Round 1 — Response
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_001",
            "type": "function",
            "function": {
              "name": "get_order",
              "arguments": "{\"order_id\": \"ORD-123\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

### Round 2 — Request (send the tool result back)
```json
{
  "model": "Qwen/Qwen3.5-2B",
  "messages": [
    {"role": "user", "content": "Check order ORD-123 for me."},
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_001",
          "type": "function",
          "function": {"name": "get_order", "arguments": "{\"order_id\": \"ORD-123\"}"}
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_001",
      "content": "{\"order_id\": \"ORD-123\", \"status\": \"shipped\", \"total\": 59.99}"
    }
  ],
  "tools": [{"type": "function", "function": {"name": "get_order", "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}}}],
  "tool_choice": "auto"
}
```

### Round 2 — Response
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Order ORD-123 has been shipped. The total is $59.99."
      },
      "finish_reason": "stop"
    }
  ]
}
```

**Rules:**
- A `role:"tool"` message **must** have `tool_call_id` matching the assistant's call.
- Echo the entire assistant message (including `tool_calls`) verbatim on the next turn.

---

## Streaming

Set `"stream": true`. The response is OpenAI-compatible SSE (`chat.completion.chunk`), ending with `data: [DONE]`. Tool-call deltas are forwarded under `choices[].delta.tool_calls`.

```bash
curl -N -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3.5-2B","messages":[{"role":"user","content":"Tell me a story"}],"stream":true}'
```

---

## Code Examples

### curl
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3.5-2B","messages":[{"role":"user","content":"Hello"}]}'
```

### Python (OpenAI SDK)

The API is OpenAI-compatible — point `base_url` at it:

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-xxxxxxxxxxxxx",
    base_url="https://llm.oriagent.com/api/public/v1",
)

# Plain chat
resp = client.chat.completions.create(
    model="Qwen/Qwen3.5-2B",
    messages=[{"role": "user", "content": "Hello"}],
)
print(resp.choices[0].message.content)

# Tool calling (your client executes the tool)
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    }
]
resp = client.chat.completions.create(
    model="Qwen/Qwen3.5-2B",
    messages=[{"role": "user", "content": "Check order ORD-123"}],
    tools=tools,
    tool_choice="auto",
)
tool_calls = resp.choices[0].message.tool_calls
# Execute get_order yourself, then send the result back as role="tool"
```

> `mode` is an OriAgent extension. With the OpenAI SDK, just pass `tools`/`tool_choice` — mode is inferred automatically.

### JavaScript / TypeScript

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "sk-xxxxxxxxxxxxx",
  baseURL: "https://llm.oriagent.com/api/public/v1",
});

const resp = await client.chat.completions.create({
  model: "Qwen/Qwen3.5-2B",
  messages: [{ role: "user", content: "Hello" }],
});
console.log(resp.choices[0].message.content);
```

---

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | `model_not_found` | Model ID does not exist |
| 400 | `invalid_tools_schema` | Tool is not `{type:"function", function:{...}}` |
| 400 | `invalid_tool_name` | `function.name` doesn't match `[a-zA-Z0-9_-]{1,64}` |
| 400 | `too_many_tools` | More than 32 tools in one request |
| 400 | `invalid_message_role` | Message role is not `system`/`user`/`assistant`/`tool` |
| 400 | `missing_tool_call_id` | A `role:"tool"` message has no `tool_call_id` |
| 401 | `unauthorized` | Invalid or missing API key |
| 403 | `model_forbidden` | Model not permitted for this API key |
| 429 | `rate_limit_error` | Rate limit exceeded (60 req/min) |
| 502 | `upstream_error` | The vLLM model server failed |

See [errors.md](./errors.md) for the full error format.
