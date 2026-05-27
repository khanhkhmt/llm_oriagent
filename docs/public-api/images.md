# Images API

## Generate Images

```
POST https://llm.oriagent.com/api/public/v1/images/generations
```

Only available when `ENABLE_IMAGE_GENERATION=true`.

### Request
```json
{
  "prompt": "A poster about AI education",
  "size": "1024x1024",
  "n": 1,
  "model": "dall-e-3"
}
```

### Response
```json
{
  "created": 1710000000,
  "data": [{"url": "/api/v1/files/xxx/content"}]
}
```

### curl Example
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/images/generations" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A futuristic city", "size": "1024x1024", "n": 1}'
```

### Limits
- Max `n`: 4
- Max prompt: 4000 characters
- Size format: `WIDTHxHEIGHT`
- Returns 403 if image generation is disabled
