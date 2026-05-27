# Testing

## Syntax Check

```bash
python3 -m compileall backend/open_webui/routers/public/
```

## Unit Tests

```bash
python3 -m pytest backend/tests/test_public_api.py -v
```

## Manual Testing

### Health Check (Production)
```bash
curl https://llm.oriagent.com/api/public/v1/health
```

> **Local Development Only:**
> ```bash
> curl http://localhost:8080/api/public/v1/health
> ```

### Authentication Test (should return 401)
```bash
curl https://llm.oriagent.com/api/public/v1/models
```

### Models with Valid API Key
```bash
curl -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  https://llm.oriagent.com/api/public/v1/models
```

### Chat Completion
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5:0.5b", "messages": [{"role": "user", "content": "Test"}]}'
```

### Invalid Model (should return 400)
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model": "nonexistent", "messages": [{"role": "user", "content": "Test"}]}'
```

### File Upload (oversized — should return 413)
```bash
dd if=/dev/zero of=/tmp/large_file bs=1M count=60
curl -X POST "https://llm.oriagent.com/api/public/v1/files" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -F "file=@/tmp/large_file"
```

## Test Checklist

- [ ] `GET /health` returns 200 without auth
- [ ] `GET /models` returns 401 without API key
- [ ] `GET /models` returns model list with valid key
- [ ] `POST /chat/completions` returns response with valid model
- [ ] `POST /chat/completions` returns 400 with invalid model
- [ ] File upload over 50MB returns 413
- [ ] User A's API key cannot access User B's files
- [ ] Rate limit returns 429 when exceeded
