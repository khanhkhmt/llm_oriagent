# Examples

## Python — Complete Chat Session

```python
import requests

BASE_URL = "https://llm.oriagent.com/api/public/v1"
API_KEY = "sk_xxxxxxxxxxxxx"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 1. Check health
health = requests.get(f"{BASE_URL}/health")
print("Health:", health.json())

# 2. List models
models = requests.get(f"{BASE_URL}/models", headers=HEADERS)
print("Models:", [m["id"] for m in models.json()["data"]])

# 3. Chat completion
chat = requests.post(
    f"{BASE_URL}/chat/completions",
    headers=HEADERS,
    json={
        "model": "qwen2.5:0.5b",
        "messages": [{"role": "user", "content": "Xin chào, bạn là ai?"}],
        "stream": False,
    },
)
print("Response:", chat.json()["choices"][0]["message"]["content"])
```

## JavaScript — Streaming Chat

```javascript
const BASE_URL = "https://llm.oriagent.com/api/public/v1";
const API_KEY = "sk_xxxxxxxxxxxxx";

async function streamChat() {
  const response = await fetch(`${BASE_URL}/chat/completions`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "qwen2.5:0.5b",
      messages: [{ role: "user", content: "Tell me a story" }],
      stream: true,
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    process.stdout.write(chunk);
  }
}

streamChat();
```

## Python — File Upload + Knowledge Query

```python
import requests

BASE_URL = "https://llm.oriagent.com/api/public/v1"
API_KEY = "sk_xxxxxxxxxxxxx"

# Upload file
with open("document.pdf", "rb") as f:
    upload = requests.post(
        f"{BASE_URL}/files",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"file": ("document.pdf", f, "application/pdf")},
        data={"purpose": "rag"},
    )
print("Uploaded:", upload.json())

# Query knowledge base
query = requests.post(
    f"{BASE_URL}/knowledge/query",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={"knowledge_id": "kb_xxx", "query": "What is AI?", "top_k": 5},
)
print("Results:", query.json())
```
