# Chat Completions API

## Create Chat Completion

Generate a chat completion response for the given messages and model.

### Endpoint

```
POST https://llm.oriagent.com/api/public/v1/chat/completions
```

### Authentication

Required. `Authorization: Bearer <api_key>`

### Permission

`public:chat:write`

### Request Body

```json
{
  "model": "qwen2.5:0.5b",
  "messages": [
    {"role": "user", "content": "Xin chào"}
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1024
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model | string | Yes | Model ID |
| messages | array | Yes | Message list (min 1) |
| stream | boolean | No | Enable SSE streaming (default: false) |
| temperature | float | No | Sampling temperature (0.0-2.0) |
| max_tokens | integer | No | Max tokens to generate |
| top_p | float | No | Top-p sampling (0.0-1.0) |
| stop | array | No | Stop sequences |

### Response (Non-Streaming)

```json
{
  "id": "chatcmpl_xxx",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "qwen2.5:0.5b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Xin chào! Tôi có thể giúp gì cho bạn?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

### Response (Streaming)

When `stream: true`, the response is Server-Sent Events (SSE) format compatible with OpenAI.

### curl Example

```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:0.5b",
    "messages": [{"role": "user", "content": "Xin chào"}],
    "stream": false
  }'
```

### JavaScript Example

```javascript
const response = await fetch(
  "https://llm.oriagent.com/api/public/v1/chat/completions",
  {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "qwen2.5:0.5b",
      messages: [{ role: "user", content: "Xin chào" }],
      stream: false
    })
  }
);
const data = await response.json();
console.log(data.choices[0].message.content);
```

### Python Example

```python
import requests

API_KEY = "sk_xxxxxxxxxxxxx"
response = requests.post(
    "https://llm.oriagent.com/api/public/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "qwen2.5:0.5b",
        "messages": [{"role": "user", "content": "Xin chào"}],
        "stream": False,
    },
)
print(response.json())
```
