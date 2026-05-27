# Models API

## List Available Models

Returns a list of models the authenticated user is allowed to use.

### Endpoint

```
GET https://llm.oriagent.com/api/public/v1/models
```

### Authentication

Required. `Authorization: Bearer <api_key>`

### Permission

`public:models:read`

### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "qwen2.5:0.5b",
      "name": "Qwen 2.5 0.5B",
      "provider": "ollama",
      "capabilities": {
        "vision": false,
        "tools": false,
        "file_upload": true
      }
    }
  ]
}
```

### curl Example

```bash
curl -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  "https://llm.oriagent.com/api/public/v1/models"
```

### JavaScript Example

```javascript
const response = await fetch(
  "https://llm.oriagent.com/api/public/v1/models",
  {
    headers: {
      "Authorization": `Bearer ${apiKey}`
    }
  }
);
const data = await response.json();
console.log(data.data); // Array of models
```

### Python Example

```python
import requests

API_KEY = "sk_xxxxxxxxxxxxx"
response = requests.get(
    "https://llm.oriagent.com/api/public/v1/models",
    headers={"Authorization": f"Bearer {API_KEY}"},
)
print(response.json())
```

### Notes

- Only models the API key owner has access to are returned
- No provider API keys or internal config are exposed
- If no models are available, returns `data: []`
