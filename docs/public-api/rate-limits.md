# Rate Limits

Limits are enforced per API key using a **sliding window** of 60 seconds.

## Limits by Endpoint

| Endpoint | Limit |
|----------|-------|
| `POST /chat/completions` | 60 req/min |
| `POST /agents/run` | 20 req/min |
| `GET /models` | 120 req/min |
| `POST /audio/transcriptions` | 20 req/min |
| `POST /audio/speech` | 30 req/min |
| `POST /images/generations` | 10 req/min |
| `POST /files` | 30 req/min |
| `POST /knowledge/query` | 60 req/min |

## Rate Limit Response

When a limit is exceeded, the API returns `HTTP 429`:

```json
{
  "success": false,
  "error": {
    "code": "rate_limit_error",
    "message": "Rate limit exceeded. Please try again later.",
    "type": "rate_limit_error"
  },
  "request_id": "req_xxx"
}
```

## Implementation

- **Redis-backed** sliding window rate limiter when Redis is available in the app state.
- **In-memory** fallback for single-instance deployments (not shared across multiple instances).
- If Redis fails, the server fails open (requests are allowed through) and logs a warning.
