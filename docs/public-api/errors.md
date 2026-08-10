# Error Handling

All Public API errors return a consistent JSON body:

```json
{
  "success": false,
  "error": {
    "code": "invalid_request",
    "message": "Human-readable description of what went wrong.",
    "type": "bad_request"
  },
  "request_id": "req_xxx"
}
```

> OpenAI-compatible success responses (`/chat/completions`) use the standard OpenAI shape, not this format.

## HTTP Status Codes

| Status | Type | Description |
|--------|------|-------------|
| 400 | `bad_request` | Invalid request body or parameters |
| 401 | `unauthorized` | Missing or invalid API key |
| 403 | `forbidden` | Insufficient permissions or feature disabled |
| 404 | `not_found` | Resource not found |
| 409 | `conflict` | Resource conflict |
| 413 | `payload_too_large` | File or payload exceeds size limit |
| 422 | `validation_error` | Request schema validation failed |
| 429 | `rate_limit_error` | Rate limit exceeded |
| 500 | `internal_error` | Internal server error |
| 502 | `upstream_error` | The vLLM model server returned an error |
| 503 | `upstream_error` | The vLLM model server is unavailable |

## Error Codes

### Authentication & Authorization

| Code | Status | Description |
|------|--------|-------------|
| `unauthorized` | 401 | Missing, malformed, or invalid API key |
| `forbidden` | 403 | API key feature disabled, insufficient role, or endpoint restricted |
| `model_forbidden` | 403 | Model is not permitted for this API key |

### Models

| Code | Status | Description |
|------|--------|-------------|
| `model_not_found` | 400 | Model ID does not exist |
| `model_forbidden` | 403 | Model exists but is not accessible to this key |

### Tool Calling (`/chat/completions`)

| Code | Status | Description |
|------|--------|-------------|
| `invalid_tools_schema` | 400 | A tool is not `{type:"function", function:{...}}` or `parameters` is not a JSON Schema object |
| `invalid_tool_name` | 400 | `function.name` doesn't match `[a-zA-Z0-9_-]{1,64}` |
| `too_many_tools` | 400 | More than 32 tools in one request |
| `duplicate_tool_name` | 400 | Two tools share the same name |
| `tool_description_too_long` | 400 | `description` exceeds 4096 characters |
| `tool_parameters_too_large` | 400 | `parameters` exceeds 16 KB serialized |
| `invalid_tool_choice` | 400 | `tool_choice` is not `"auto"`, `"none"`, `"required"`, or a valid named-tool object |

### Messages

| Code | Status | Description |
|------|--------|-------------|
| `invalid_message_role` | 400 | Role is not `system`, `user`, `assistant`, or `tool` |
| `missing_tool_call_id` | 400 | A `role:"tool"` message has no `tool_call_id` |
| `invalid_tool_calls` | 400 | An assistant `tool_calls` entry is missing `id`, `type`, `function.name`, or `function.arguments` |

### Agents (`/agents/run`)

| Code | Status | Description |
|------|--------|-------------|
| `unknown_tool` | 400 | `allowed_tools` references an unregistered internal tool |

### Rate Limits

| Code | Status | Description |
|------|--------|-------------|
| `rate_limit_error` | 429 | Per-key rate limit exceeded for this endpoint |

### Upstream

| Code | Status | Description |
|------|--------|-------------|
| `upstream_error` | 502/503 | The vLLM model server failed or is unavailable |

## Using `request_id`

Every response (success and error) includes a `request_id`. Send this ID when reporting issues — it links your request to server logs.

You can also set your own correlation ID by sending the `X-Request-ID` header:
```
X-Request-ID: my-trace-id-abc123
```
It is echoed back in the response headers and in error bodies.

## Security

- Stack traces are **never** included in error responses.
- Internal file paths are **never** revealed.
- Provider API keys are **never** included in error details.
- Model reasoning (`<think>…</think>`) is stripped from all responses.
