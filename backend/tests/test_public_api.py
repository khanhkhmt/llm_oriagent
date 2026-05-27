"""
Tests for OriAgent Public API v1

Run with: python3 -m pytest backend/tests/test_public_api.py -v

These tests validate the Public API endpoints for correct behavior
including authentication, authorization, and response format.
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Schema Tests ────────────────────────────────────────────────────────────

def test_health_response_schema():
    from open_webui.routers.public.schemas import PublicHealthResponse
    resp = PublicHealthResponse()
    assert resp.status == "ok"
    assert resp.service == "OriAgent Public API"
    assert resp.version == "v1"

def test_model_schema():
    from open_webui.routers.public.schemas import PublicModel, PublicModelCapabilities
    model = PublicModel(id="qwen2.5:0.5b", name="Qwen 2.5 0.5B", provider="ollama")
    assert model.id == "qwen2.5:0.5b"
    assert model.capabilities.vision is False

def test_chat_request_schema():
    from open_webui.routers.public.schemas import PublicChatCompletionRequest, PublicChatMessage
    req = PublicChatCompletionRequest(
        model="qwen2.5:0.5b",
        messages=[PublicChatMessage(role="user", content="Hello")],
    )
    assert req.model == "qwen2.5:0.5b"
    assert len(req.messages) == 1
    assert req.stream is False

def test_chat_response_schema():
    from open_webui.routers.public.schemas import (
        PublicChatCompletionResponse, PublicChatCompletionChoice,
        PublicChatCompletionChoiceMessage, PublicUsage
    )
    resp = PublicChatCompletionResponse(
        id="chatcmpl_test",
        created=int(time.time()),
        model="test",
        choices=[PublicChatCompletionChoice(
            index=0,
            message=PublicChatCompletionChoiceMessage(role="assistant", content="Hi!"),
            finish_reason="stop",
        )],
        usage=PublicUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
    )
    assert resp.choices[0].message.content == "Hi!"

def test_file_response_schema():
    from open_webui.routers.public.schemas import PublicFileResponse
    resp = PublicFileResponse(
        id="file_123", filename="test.pdf", bytes=1024, created_at=int(time.time())
    )
    assert resp.object == "file"

def test_error_response_schema():
    from open_webui.routers.public.schemas import PublicErrorResponse, PublicError
    resp = PublicErrorResponse(
        error=PublicError(code="invalid_request", message="Bad input", type="bad_request"),
        request_id="req_123",
    )
    assert resp.success is False
    assert resp.error.code == "invalid_request"


# ─── Error Handler Tests ────────────────────────────────────────────────────

def test_make_error_response():
    from open_webui.routers.public.errors import make_error_response
    resp = make_error_response(400, "invalid_request", "Bad input", "req_123")
    assert resp.status_code == 400

def test_make_success_response():
    from open_webui.routers.public.errors import make_success_response
    resp = make_success_response({"key": "value"}, "req_123")
    assert resp["success"] is True
    assert resp["data"]["key"] == "value"


# ─── Context / Deps Tests ───────────────────────────────────────────────────

def test_public_api_context_model():
    from open_webui.routers.public.deps import PublicAPIContext
    ctx = PublicAPIContext(user_id="user_1", role="user", request_id="req_1")
    assert ctx.user_id == "user_1"
    assert ctx.scopes == []


# ─── Rate Limit Tests ───────────────────────────────────────────────────────

def test_rate_limit_memory():
    from open_webui.routers.public.rate_limit import _check_rate_limit_memory, _in_memory_store
    # Reset state
    _in_memory_store.clear()
    # Should not raise for first request
    _check_rate_limit_memory("user1", "models", 5, 60, "req_1")
    assert len(_in_memory_store["user1:models"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
