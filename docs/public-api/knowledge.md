# Knowledge API

Query a knowledge base (RAG — Retrieval-Augmented Generation). Returns the most relevant text chunks along with their source information and relevance scores.

## Query a Knowledge Base

```
POST https://llm.oriagent.com/api/public/v1/knowledge/query
Content-Type: application/json
Authorization: Bearer sk-xxxxxxxxxxxxx
```

### Request

```json
{
  "knowledge_id": "kb_abc123",
  "query": "What is machine learning?",
  "top_k": 5,
  "rerank": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `knowledge_id` | string | Yes | Knowledge base identifier |
| `query` | string | Yes | Natural language search query |
| `top_k` | integer | No | Number of results to return, 1–50 (default `5`) |
| `rerank` | boolean | No | Re-rank results for better relevance (default `true`) |

### Response

```json
{
  "object": "knowledge.query",
  "data": [
    {
      "content": "Machine learning is a branch of artificial intelligence...",
      "score": 0.92,
      "source": {
        "file_id": "file_abc123",
        "filename": "intro-to-ml.pdf",
        "page": 3
      }
    },
    {
      "content": "Supervised learning involves training a model on labeled data...",
      "score": 0.87,
      "source": {
        "file_id": "file_abc123",
        "filename": "intro-to-ml.pdf",
        "page": 5
      }
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data[].content` | string | Matched text chunk |
| `data[].score` | float | Relevance score (higher is better) |
| `data[].source.file_id` | string | Source file identifier |
| `data[].source.filename` | string | Source filename |
| `data[].source.page` | integer | Source page number (if applicable) |

### Examples

**curl**
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/knowledge/query" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"knowledge_id": "kb_abc123", "query": "What is machine learning?", "top_k": 5}'
```

**Python**
```python
import requests

resp = requests.post(
    "https://llm.oriagent.com/api/public/v1/knowledge/query",
    headers={"Authorization": "Bearer sk-xxxxxxxxxxxxx"},
    json={
        "knowledge_id": "kb_abc123",
        "query": "What is machine learning?",
        "top_k": 5,
        "rerank": True,
    },
)
for result in resp.json()["data"]:
    print(f"[{result['score']:.2f}] {result['content'][:100]}")
```

**JavaScript**
```javascript
const resp = await fetch("https://llm.oriagent.com/api/public/v1/knowledge/query", {
  method: "POST",
  headers: {
    "Authorization": "Bearer sk-xxxxxxxxxxxxx",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    knowledge_id: "kb_abc123",
    query: "What is machine learning?",
    top_k: 5,
  }),
});
const { data } = await resp.json();
console.log(data);
```

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | `bad_request` | Invalid request body |
| 401 | `unauthorized` | Invalid or missing API key |
| 403 | `forbidden` | Knowledge base belongs to another user |
| 404 | `not_found` | Knowledge base ID does not exist |
| 429 | `rate_limit_error` | Rate limit exceeded (60 req/min) |

### Security

- Only the knowledge base owner can query it.
- Local file paths are never exposed — only `file_id` and `filename`.
- `top_k` is capped at 50.
