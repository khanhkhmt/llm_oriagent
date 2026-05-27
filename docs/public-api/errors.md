# Error Handling

All Public API errors return a consistent JSON format:

```json
{
  "success": false,
  "error": {
    "code": "invalid_request",
    "message": "Human readable message",
    "type": "bad_request"
  },
  "request_id": "req_xxx"
}
```

## HTTP Status Codes

| Status | Type | Description |
|--------|------|-------------|
| 400 | `bad_request` | Invalid request body or parameters |
| 401 | `unauthorized` | Missing or invalid API key |
| 403 | `forbidden` | Insufficient permissions or feature disabled |
| 404 | `not_found` | Resource not found |
| 409 | `conflict` | Resource conflict |
| 413 | `payload_too_large` | File or payload exceeds size limit |
| 422 | `validation_error` | Request validation failed |
| 429 | `rate_limit_error` | Rate limit exceeded |
| 500 | `internal_error` | Internal server error |

## Security

- Stack traces are **never** exposed in error responses
- Internal file paths are **never** revealed
- Provider API keys are **never** included in error details
