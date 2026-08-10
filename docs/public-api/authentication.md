# Authentication

All Public API endpoints except `/health` require an API key passed as a Bearer token.

## Getting an API Key

1. Log into OriAgent at `https://llm.oriagent.com`
2. Go to **Settings → Account → API Keys**
3. Click **Generate New Key**
4. Copy and store your key securely — it is shown only once

Keys have the format `sk-xxxxxxxxxxxx`.

## Using the API Key

Include the key in every request:

```
Authorization: Bearer sk-xxxxxxxxxxxxx
```

**curl:**
```bash
curl -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  https://llm.oriagent.com/api/public/v1/models
```

**Python:**
```python
import requests

headers = {"Authorization": "Bearer sk-xxxxxxxxxxxxx"}
resp = requests.get("https://llm.oriagent.com/api/public/v1/models", headers=headers)
```

**JavaScript:**
```javascript
const resp = await fetch("https://llm.oriagent.com/api/public/v1/models", {
  headers: { "Authorization": "Bearer sk-xxxxxxxxxxxxx" },
});
```

## Requirements

- Key must start with `sk-`
- Key must belong to an active user with role `user` or `admin`
- The API key feature must be enabled by the administrator

## Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 401 | `unauthorized` | Missing, malformed, or invalid API key |
| 403 | `forbidden` | API key feature disabled, insufficient role, or endpoint restricted |

## Security

- **Never** share or commit API keys to version control
- API keys are tied to a specific user — all requests are attributed to that user
- The server never logs or returns API keys in responses
- Regenerate a key immediately if it may have been exposed
