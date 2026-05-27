# Knowledge API

## Query Knowledge Base

```
POST https://llm.oriagent.com/api/public/v1/knowledge/query
```

### Request
```json
{
  "knowledge_id": "kb_xxx",
  "query": "What is machine learning?",
  "top_k": 5,
  "rerank": true
}
```

### Response
```json
{
  "object": "knowledge.query",
  "data": [
    {
      "content": "Machine learning is...",
      "score": 0.89,
      "source": {
        "file_id": "file_xxx",
        "filename": "document.pdf",
        "page": 2
      }
    }
  ]
}
```

### curl Example
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/knowledge/query" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"knowledge_id": "kb_xxx", "query": "What is AI?", "top_k": 5}'
```

### Security
- Only the knowledge base owner can query it
- No local file paths exposed
- top_k limited to 50
