# Images API

Generate images from a text prompt.

> Only available when `ENABLE_IMAGE_GENERATION=true` on the server.

## Generate Images

```
POST https://llm.oriagent.com/api/public/v1/images/generations
Content-Type: application/json
Authorization: Bearer sk-xxxxxxxxxxxxx
```

### Request

```json
{
  "prompt": "A futuristic city skyline at sunset",
  "size": "1024x1024",
  "n": 1,
  "model": "dall-e-3"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | Image generation prompt (max 4000 characters) |
| `size` | string | No | Image dimensions as `WIDTHxHEIGHT` (default `"1024x1024"`) |
| `n` | integer | No | Number of images to generate, 1–4 (default `1`) |
| `model` | string | No | Image model to use (server-configured default if omitted) |

### Response

```json
{
  "created": 1710000000,
  "data": [
    {
      "url": "/api/v1/files/file_abc123/content"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `created` | integer | Unix timestamp of generation |
| `data[].url` | string | URL to retrieve the generated image |

### Examples

**curl**
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/images/generations" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A futuristic city skyline at sunset", "size": "1024x1024", "n": 1}'
```

**Python**
```python
import requests

resp = requests.post(
    "https://llm.oriagent.com/api/public/v1/images/generations",
    headers={"Authorization": "Bearer sk-xxxxxxxxxxxxx"},
    json={
        "prompt": "A futuristic city skyline at sunset",
        "size": "1024x1024",
        "n": 1,
    },
)
for image in resp.json()["data"]:
    print(image["url"])
```

**JavaScript**
```javascript
const resp = await fetch("https://llm.oriagent.com/api/public/v1/images/generations", {
  method: "POST",
  headers: {
    "Authorization": "Bearer sk-xxxxxxxxxxxxx",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    prompt: "A futuristic city skyline at sunset",
    size: "1024x1024",
    n: 1,
  }),
});
const { data } = await resp.json();
console.log(data[0].url);
```

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | `bad_request` | Invalid request body or unsupported size |
| 401 | `unauthorized` | Invalid or missing API key |
| 403 | `forbidden` | Image generation is disabled on this server |
| 429 | `rate_limit_error` | Rate limit exceeded (10 req/min) |
