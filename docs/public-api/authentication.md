# Authentication

## API Key Authentication

All Public API endpoints (except `/health`) require authentication using an API key.

### Getting an API Key

1. Log into OriAgent at `https://llm.oriagent.com`
2. Navigate to **Settings** → **Account** → **API Keys**
3. Click **Generate New Key**
4. Copy and securely store your API key (format: `sk-xxxxxxxxxxxx`)

### Using the API Key

Include the API key in the `Authorization` header:

```
Authorization: Bearer sk_xxxxxxxxxxxxx
```

### Requirements

- API key must start with `sk-`
- API key must belong to an active user
- User must have role `user` or `admin`
- API key feature must be enabled by the administrator
- If endpoint restrictions are enabled, the Public API path must be in the allowlist

### Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 401 | `unauthorized` | Missing or invalid API key |
| 403 | `forbidden` | API key feature disabled, insufficient role, or endpoint restricted |

### Example

```bash
curl -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  https://llm.oriagent.com/api/public/v1/models
```

### Security Notes

- **Never share** your API key publicly
- **Never commit** API keys to version control
- API keys are tied to a specific user — all actions are attributed to that user
- API keys can be regenerated from the Settings page
- The server **never** returns API keys in responses
- The server **never** logs API keys or Authorization headers
