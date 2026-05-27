# Files API

## Upload File

```
POST https://llm.oriagent.com/api/public/v1/files
```

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | File to upload |
| purpose | string | No | Purpose: "rag", "chat", "general" |

### curl Example
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/files" \
  -H "Authorization: Bearer sk_xxxxxxxxxxxxx" \
  -F "file=@document.pdf" \
  -F "purpose=rag"
```

### Response
```json
{
  "id": "file_xxx",
  "object": "file",
  "filename": "document.pdf",
  "bytes": 123456,
  "mime_type": "application/pdf",
  "created_at": 1710000000
}
```

## Get File Metadata

```
GET https://llm.oriagent.com/api/public/v1/files/{file_id}
```

Only the file owner can access metadata.

## Delete File

```
DELETE https://llm.oriagent.com/api/public/v1/files/{file_id}
```

Only the file owner can delete. Response:
```json
{"success": true, "id": "file_xxx", "deleted": true}
```

### Security
- Filename validation (anti path-traversal)
- MIME type and extension validation
- Max file size: 50MB
- Dangerous extensions blocked (exe, bat, sh, etc.)
- Files are owned by API key user — cross-user access is denied
