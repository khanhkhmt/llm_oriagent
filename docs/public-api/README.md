# OriAgent Public API Documentation

## Overview

The OriAgent Public API provides a stable, secure, and easy-to-use interface for third-party integrations. It allows external applications to use OriAgent as an AI platform for chat completions, file management, knowledge queries, audio processing, and image generation.

## Base URL

**Production:**
```
https://llm.oriagent.com/api/public/v1
```

> **Local Development Only:**
> ```
> http://localhost:8080/api/public/v1
> ```

## Authentication

All endpoints (except `/health`) require authentication via API key:

```
Authorization: Bearer sk_xxxxxxxxxxxxx
```

See [Authentication](./authentication.md) for details.

## Available Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | No |
| GET | `/models` | List available models | Yes |
| POST | `/chat/completions` | Chat completion (streaming & non-streaming) | Yes |
| POST | `/files` | Upload a file | Yes |
| GET | `/files/{file_id}` | Get file metadata | Yes |
| DELETE | `/files/{file_id}` | Delete a file | Yes |
| POST | `/audio/transcriptions` | Speech-to-text | Yes |
| POST | `/audio/speech` | Text-to-speech | Yes |
| POST | `/knowledge/query` | Query knowledge base (RAG) | Yes |
| POST | `/images/generations` | Generate images | Yes |

## Quick Start

### 1. Get an API Key

Log into OriAgent → Settings → Account → API Keys → Generate new key.

### 2. Test the Health Endpoint

```bash
curl https://llm.oriagent.com/api/public/v1/health
```

### 3. List Models

```bash
curl -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  https://llm.oriagent.com/api/public/v1/models
```

### 4. Send a Chat Message

```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:0.5b",
    "messages": [{"role": "user", "content": "Xin chào"}],
    "stream": false
  }'
```

## Documentation Index

- [Authentication](./authentication.md)
- [Models API](./models.md)
- [Chat Completions API](./chat-completions.md)
- [Files API](./files.md)
- [Knowledge API](./knowledge.md)
- [Audio API](./audio.md)
- [Images API](./images.md)
- [Error Handling](./errors.md)
- [Rate Limits](./rate-limits.md)
- [Examples](./examples.md)
- [Testing](./testing.md)
- [OpenAPI Docs](./openapi.md)

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "request_id": "req_xxx"
}
```

### Error Response
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

> **Note:** OpenAI-compatible endpoints like `/chat/completions` use the standard OpenAI response format.
