# Audio API

## Speech-to-Text (Transcription)

Transcribe an audio file to text.

```
POST https://llm.oriagent.com/api/public/v1/audio/transcriptions
Content-Type: multipart/form-data
Authorization: Bearer sk-xxxxxxxxxxxxx
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Audio file to transcribe (max 25 MB) |
| `language` | string | No | BCP-47 language code hint, e.g. `"en"`, `"vi"` |

### Response
```json
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "language": "en"
}
```

### curl
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/audio/transcriptions" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -F "file=@recording.mp3" \
  -F "language=en"
```

### Python
```python
import requests

with open("recording.mp3", "rb") as f:
    resp = requests.post(
        "https://llm.oriagent.com/api/public/v1/audio/transcriptions",
        headers={"Authorization": "Bearer sk-xxxxxxxxxxxxx"},
        files={"file": ("recording.mp3", f, "audio/mpeg")},
        data={"language": "en"},
    )
print(resp.json()["text"])
```

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | `bad_request` | Unsupported file format |
| 413 | `payload_too_large` | File exceeds 25 MB |
| 429 | `rate_limit_error` | Rate limit exceeded (20 req/min) |

---

## Text-to-Speech

Synthesize speech from text. Returns binary audio content.

```
POST https://llm.oriagent.com/api/public/v1/audio/speech
Content-Type: application/json
Authorization: Bearer sk-xxxxxxxxxxxxx
```

### Request
```json
{
  "input": "Hello, I am OriAgent.",
  "voice": "default",
  "format": "mp3"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input` | string | Yes | Text to synthesize (max 4096 characters) |
| `voice` | string | No | Voice identifier (default: `"default"`) |
| `format` | string | No | Output format (default: `"mp3"`) |

### Response

Returns `audio/mpeg` binary content (or the appropriate MIME type for the requested format).

### curl
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/audio/speech" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, I am OriAgent.", "voice": "default"}' \
  --output speech.mp3
```

### Python
```python
import requests

resp = requests.post(
    "https://llm.oriagent.com/api/public/v1/audio/speech",
    headers={"Authorization": "Bearer sk-xxxxxxxxxxxxx"},
    json={"input": "Hello, I am OriAgent.", "voice": "default"},
)
with open("speech.mp3", "wb") as f:
    f.write(resp.content)
```

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | `bad_request` | Invalid request body |
| 429 | `rate_limit_error` | Rate limit exceeded (30 req/min) |
