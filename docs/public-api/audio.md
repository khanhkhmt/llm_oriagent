# Audio API

## Transcribe Audio (STT)

```
POST https://llm.oriagent.com/api/public/v1/audio/transcriptions
```

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | Audio file (max 25MB) |
| language | string | No | Language code (e.g., "vi", "en") |

### curl Example
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/audio/transcriptions" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -F "file=@audio.mp3" \
  -F "language=vi"
```

### Response
```json
{"text": "Xin chào, đây là nội dung audio", "language": "vi"}
```

## Text-to-Speech (TTS)

```
POST https://llm.oriagent.com/api/public/v1/audio/speech
```

### Request
```json
{"input": "Xin chào, tôi là OriAgent.", "voice": "default", "format": "mp3"}
```

### Response
Returns `audio/mpeg` binary content.

### curl Example
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/audio/speech" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "voice": "default"}' \
  --output speech.mp3
```
