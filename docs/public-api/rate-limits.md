# Rate Limits

## Default Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/chat/completions` | 60 requests | per minute per API key |
| `/audio/transcriptions` | 20 requests | per minute per API key |
| `/images/generations` | 10 requests | per minute per API key |
| `/files` | 30 requests | per minute per API key |
| `/models` | 120 requests | per minute per API key |
| `/knowledge/query` | 60 requests | per minute per API key |
| `/audio/speech` | 30 requests | per minute per API key |

## Rate Limit Response

When the rate limit is exceeded:

```
HTTP 429 Too Many Requests
```

```json
{
  "success": false,
  "error": {
    "code": "rate_limited",
    "message": "Rate limit exceeded. Please try again later.",
    "type": "rate_limit_error"
  },
  "request_id": "req_xxx"
}
```

## Implementation

- **Redis-backed** sliding window rate limiter when Redis is available
- **In-memory** fallback for single-instance deployments
- Rate limits are enforced per API key (user)
