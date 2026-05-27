# OpenAPI / Swagger Documentation

## Accessing OpenAPI Docs

The OriAgent Public API endpoints are included in the FastAPI OpenAPI schema.

### Development Mode

When `ENV=dev`, Swagger docs are available at:

```
http://localhost:8080/docs
```

The Public API endpoints appear under the **"Public API"** tag.

### Production

In production (`ENV=prod`), Swagger UI and OpenAPI JSON are **disabled by default** for security:

```python
# main.py
app = FastAPI(
    docs_url='/docs' if ENV == 'dev' else None,
    openapi_url='/openapi.json' if ENV == 'dev' else None,
)
```

> **Note:** Do NOT assume production Swagger docs are available. The OpenAPI spec is only served in development mode.

## Schema Documentation

All Public API endpoints have:

- **Summary** — Short description
- **Description** — Detailed explanation
- **Response models** — Pydantic schema with Field descriptions
- **Examples** — In Pydantic schema `examples` parameter
- **Status codes** — Documented in `responses` parameter

## Tags

All Public API endpoints are tagged with:

- `Public API` (main tag)
- `Public API - Models`
- `Public API - Chat`
- `Public API - Files`
- `Public API - Audio`
- `Public API - Knowledge`
- `Public API - Images`
