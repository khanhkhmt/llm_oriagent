# OpenAPI / Swagger

## Development

When `ENV=dev`, Swagger UI is available at:

```
http://localhost:8080/docs
```

The OpenAPI JSON spec is at:

```
http://localhost:8080/openapi.json
```

Public API endpoints appear under the **"Public API"** tags in the spec.

## Production

In production (`ENV=prod`), Swagger UI and the OpenAPI JSON endpoint are **disabled by default**:

```python
# main.py
app = FastAPI(
    docs_url="/docs" if ENV == "dev" else None,
    openapi_url="/openapi.json" if ENV == "dev" else None,
)
```

Do not assume production Swagger docs are available.

## Schema Coverage

All Public API endpoints include:

- **Summary** — short one-line description
- **Description** — detailed explanation
- **Request body** — Pydantic schema with field descriptions and examples
- **Response models** — typed Pydantic schemas
- **Status codes** — documented in the `responses` parameter

## Tags

| Tag | Endpoints |
|-----|-----------|
| `Public API` | `/health` |
| `Public API - Models` | `/models` |
| `Public API - Chat` | `/chat/completions` |
| `Public API - Agents` | `/agents/run` |
| `Public API - Files` | `/files`, `/files/{id}` |
| `Public API - Audio` | `/audio/transcriptions`, `/audio/speech` |
| `Public API - Knowledge` | `/knowledge/query` |
| `Public API - Images` | `/images/generations` |
