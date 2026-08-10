# Files API

Upload, retrieve, and delete files. Files can be used for RAG (Retrieval-Augmented Generation) or as context in chat.

## Upload a File

```
POST https://llm.oriagent.com/api/public/v1/files
Content-Type: multipart/form-data
Authorization: Bearer sk-xxxxxxxxxxxxx
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | File to upload |
| `purpose` | string | No | `"rag"`, `"chat"`, or `"general"` (default: `"general"`) |

**Limits:** Max 50 MB per file. Dangerous extensions (`.exe`, `.bat`, `.sh`, etc.) are blocked.

### Response
```json
{
  "id": "file_abc123",
  "object": "file",
  "filename": "document.pdf",
  "bytes": 123456,
  "mime_type": "application/pdf",
  "created_at": 1710000000
}
```

### curl
```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/files" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  -F "file=@document.pdf" \
  -F "purpose=rag"
```

### Python
```python
import requests

with open("document.pdf", "rb") as f:
    resp = requests.post(
        "https://llm.oriagent.com/api/public/v1/files",
        headers={"Authorization": "Bearer sk-xxxxxxxxxxxxx"},
        files={"file": ("document.pdf", f, "application/pdf")},
        data={"purpose": "rag"},
    )
print(resp.json()["id"])
```

---

## Get File Metadata

```
GET https://llm.oriagent.com/api/public/v1/files/{file_id}
Authorization: Bearer sk-xxxxxxxxxxxxx
```

Returns the same shape as the upload response. Only the file owner can retrieve metadata.

### curl
```bash
curl -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  "https://llm.oriagent.com/api/public/v1/files/file_abc123"
```

---

## Delete a File

```
DELETE https://llm.oriagent.com/api/public/v1/files/{file_id}
Authorization: Bearer sk-xxxxxxxxxxxxx
```

Only the file owner can delete. Returns:
```json
{"success": true, "id": "file_abc123", "deleted": true}
```

### curl
```bash
curl -X DELETE -H "Authorization: Bearer sk-xxxxxxxxxxxxx" \
  "https://llm.oriagent.com/api/public/v1/files/file_abc123"
```

---

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | `bad_request` | Invalid file type or malformed request |
| 401 | `unauthorized` | Invalid or missing API key |
| 403 | `forbidden` | File belongs to another user |
| 404 | `not_found` | File ID does not exist |
| 413 | `payload_too_large` | File exceeds the 50 MB limit |
| 429 | `rate_limit_error` | Rate limit exceeded (30 req/min) |

## Security

- Filename validation prevents path-traversal attacks.
- MIME type and file extension are validated on upload.
- Files are strictly owned by the uploading API key's user — cross-user access is denied.
