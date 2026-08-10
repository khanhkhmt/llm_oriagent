# Testing Guide

## Automated Tests

### Syntax Check
```bash
python3 -m compileall backend/open_webui/routers/public/
```

### Unit Tests
```bash
python3 -m pytest backend/tests/test_public_api.py -v
```

---

## Manual Testing

### Health Check
```bash
curl https://llm.oriagent.com/api/public/v1/health
```
Expected: `{"status": "ok", "service": "OriAgent Public API", "version": "v1"}`

### Authentication — No Key (expect 401)
```bash
curl https://llm.oriagent.com/api/public/v1/models
```

### Authentication — Valid Key
```bash
curl -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  https://llm.oriagent.com/api/public/v1/models
```
Expected: `{"object": "list", "data": [...]}`

### Chat Completion
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen3.5-2B", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Invalid Model (expect 400)
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model": "nonexistent-model", "messages": [{"role": "user", "content": "Hello"}]}'
```
Expected: `{"success": false, "error": {"code": "model_not_found", ...}}`

### Agent Run
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/agents/run" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen3.5-2B", "messages": [{"role": "user", "content": "What time is it?"}], "allowed_tools": ["get_time"]}'
```

### Rate Limit (expect 429)

Send more than 60 requests in 60 seconds to `/chat/completions`.

### Oversized File Upload (expect 413)
```bash
dd if=/dev/zero of=/tmp/large_file bs=1M count=60
curl -X POST "https://llm.oriagent.com/api/public/v1/files" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -F "file=@/tmp/large_file"
```

---

## Test Checklist

- [ ] `GET /health` returns 200 without auth
- [ ] `GET /models` returns 401 without API key
- [ ] `GET /models` returns model list with a valid key
- [ ] `POST /chat/completions` returns a completion with a valid model
- [ ] `POST /chat/completions` returns 400 with an unknown model
- [ ] `POST /agents/run` returns an answer with `allowed_tools: ["get_time"]`
- [ ] `POST /agents/run` returns 400 with an unknown tool name
- [ ] File upload over 50 MB returns 413
- [ ] User A's API key cannot access User B's files (403)
- [ ] Rate limit returns 429 when exceeded

---

## Local Development

When running locally, replace the base URL:

```bash
curl http://localhost:8080/api/public/v1/health
```

Swagger UI is available at `http://localhost:8080/docs` when `ENV=dev`.
