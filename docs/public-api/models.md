# Models API

List the models your API key is permitted to use.

## GET /models

```
GET https://llm.oriagent.com/api/public/v1/models
```

**Authentication:** Required — `Authorization: Bearer <api-key>`

### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen3.5-2B",
      "name": "Qwen 3.5 2B",
      "provider": "openai",
      "capabilities": {
        "vision": false,
        "tools": true,
        "file_upload": true
      }
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Model identifier — use this as the `model` field in requests |
| `name` | string | Human-readable display name |
| `provider` | string | Backend provider: `ollama`, `openai`, `pipeline`, or `unknown` |
| `capabilities.vision` | boolean | Accepts image inputs |
| `capabilities.tools` | boolean | Supports function/tool calling |
| `capabilities.file_upload` | boolean | Accepts file uploads in context |

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 401 | `unauthorized` | Missing or invalid API key |
| 403 | `forbidden` | API key feature disabled |
| 429 | `rate_limit_error` | Rate limit exceeded (120 req/min) |

### Examples

**curl**
```bash
curl -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  "https://llm.oriagent.com/api/public/v1/models"
```

**Python**
```python
import requests

resp = requests.get(
    "https://llm.oriagent.com/api/public/v1/models",
    headers={"Authorization": "Bearer sk-xxxxxxxxxxxxx"},
)
for model in resp.json()["data"]:
    print(model["id"], model["capabilities"])
```

**JavaScript**
```javascript
const resp = await fetch("https://llm.oriagent.com/api/public/v1/models", {
  headers: { "Authorization": "Bearer sk-xxxxxxxxxxxxx" },
});
const { data } = await resp.json();
console.log(data.map(m => m.id));
```

### Notes

- Only models the API key owner can access are returned.
- Filter pipelines are excluded from the list.
- If no models are accessible, `data` is an empty array.
