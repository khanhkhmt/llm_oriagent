# Examples

End-to-end code samples for common use cases.

## Python — Complete Session

Health check, list models, and send a chat message.

```python
import requests

BASE_URL = "https://llm.oriagent.com/api/public/v1"
API_KEY = "sk-xxxxxxxxxxxxx"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 1. Health check (no auth required)
health = requests.get(f"{BASE_URL}/health")
print("Health:", health.json())  # {"status": "ok", ...}

# 2. List accessible models
models = requests.get(f"{BASE_URL}/models", headers=HEADERS)
model_ids = [m["id"] for m in models.json()["data"]]
print("Models:", model_ids)

# 3. Chat completion
resp = requests.post(
    f"{BASE_URL}/chat/completions",
    headers=HEADERS,
    json={
        "model": model_ids[0],
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
    },
)
print("Answer:", resp.json()["choices"][0]["message"]["content"])
```

---

## Python — Tool Calling (Client-Managed Loop)

```python
import json
import requests

BASE_URL = "https://llm.oriagent.com/api/public/v1"
HEADERS = {
    "Authorization": "Bearer sk-xxxxxxxxxxxxx",
    "Content-Type": "application/json",
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"],
            },
        },
    }
]

def get_weather(city: str) -> str:
    # Your actual implementation here
    return json.dumps({"city": city, "temperature": 22, "condition": "sunny"})

messages = [{"role": "user", "content": "What is the weather like in Paris?"}]

while True:
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=HEADERS,
        json={"model": "Qwen/Qwen3.5-2B", "messages": messages, "tools": TOOLS, "tool_choice": "auto"},
    ).json()

    choice = resp["choices"][0]
    msg = choice["message"]
    messages.append(msg)

    if choice["finish_reason"] == "tool_calls":
        for call in msg["tool_calls"]:
            fn_name = call["function"]["name"]
            fn_args = json.loads(call["function"]["arguments"])
            result = get_weather(**fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": result,
            })
    else:
        print("Final answer:", msg["content"])
        break
```

---

## Python — Server-Side Agent (`/agents/run`)

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
print("Answer:", data["answer"])
print("Steps:", data["steps"])
for step in data["tool_trace"]:
    print(f"  Tool: {step['tool_name']} | Status: {step['status']}")
```

---

## JavaScript — Streaming Chat

```javascript
const BASE_URL = "https://llm.oriagent.com/api/public/v1";
const API_KEY = "sk-xxxxxxxxxxxxx";

async function streamChat(prompt) {
  const response = await fetch(`${BASE_URL}/chat/completions`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "Qwen/Qwen3.5-2B",
      messages: [{ role: "user", content: prompt }],
      stream: true,
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    for (const line of text.split("\n")) {
      if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
      const chunk = JSON.parse(line.slice(6));
      const delta = chunk.choices[0]?.delta?.content;
      if (delta) process.stdout.write(delta);
    }
  }
  console.log();
}

streamChat("Explain quantum computing in simple terms.");
```

---

## Python — File Upload and Knowledge Query

```python
import requests

BASE_URL = "https://llm.oriagent.com/api/public/v1"
HEADERS = {"Authorization": "Bearer sk-xxxxxxxxxxxxx"}

# Upload a document
with open("research-paper.pdf", "rb") as f:
    upload = requests.post(
        f"{BASE_URL}/files",
        headers=HEADERS,
        files={"file": ("research-paper.pdf", f, "application/pdf")},
        data={"purpose": "rag"},
    )
file_id = upload.json()["id"]
print("Uploaded file:", file_id)

# Query a knowledge base
query = requests.post(
    f"{BASE_URL}/knowledge/query",
    headers={**HEADERS, "Content-Type": "application/json"},
    json={
        "knowledge_id": "kb_abc123",
        "query": "What are the main findings?",
        "top_k": 3,
    },
)
for result in query.json()["data"]:
    print(f"[{result['score']:.2f}] {result['content'][:120]}")
```

---

## OpenAI SDK Compatibility

The OriAgent Public API is fully compatible with the OpenAI Python and JavaScript SDKs. Just override `base_url`:

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-xxxxxxxxxxxxx",
    base_url="https://llm.oriagent.com/api/public/v1",
)

resp = client.chat.completions.create(
    model="Qwen/Qwen3.5-2B",
    messages=[{"role": "user", "content": "Hello"}],
)
print(resp.choices[0].message.content)
```

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
