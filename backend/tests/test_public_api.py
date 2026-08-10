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
    model = PublicModel(id="Qwen/Qwen3.5-2B", name="Qwen 3.5 2B", provider="openai")
    assert model.id == "Qwen/Qwen3.5-2B"
    assert model.capabilities.vision is False

def test_chat_request_schema():
    from open_webui.routers.public.schemas import PublicChatCompletionRequest, PublicChatMessage
    req = PublicChatCompletionRequest(
        model="Qwen/Qwen3.5-2B",
        messages=[PublicChatMessage(role="user", content="Hello")],
    )
    assert req.model == "Qwen/Qwen3.5-2B"
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


# ─── Tool calling: request classification ────────────────────────────────────

def test_classify_chat_default():
    from open_webui.routers.public.tools_schema import classify_request, MODE_CHAT
    assert classify_request(None, None, None, [{"role": "user", "content": "hi"}]) == MODE_CHAT

def test_classify_tools_present():
    from open_webui.routers.public.tools_schema import classify_request, MODE_EXTERNAL_TOOL_CALLING
    tools = [{"type": "function", "function": {"name": "f"}}]
    assert classify_request(None, tools, None, [{"role": "user", "content": "hi"}]) == MODE_EXTERNAL_TOOL_CALLING

def test_classify_tool_message_present():
    from open_webui.routers.public.tools_schema import classify_request, MODE_EXTERNAL_TOOL_CALLING
    msgs = [{"role": "user", "content": "hi"}, {"role": "tool", "tool_call_id": "c1", "content": "obs"}]
    assert classify_request(None, None, None, msgs) == MODE_EXTERNAL_TOOL_CALLING

def test_classify_explicit_mode_wins():
    from open_webui.routers.public.tools_schema import classify_request
    tools = [{"type": "function", "function": {"name": "f"}}]
    assert classify_request("chat", tools, None, [{"role": "user", "content": "hi"}]) == "chat"


# ─── Tool calling: validators ────────────────────────────────────────────────

def test_validate_tools_ok():
    from open_webui.routers.public.tools_schema import validate_tools
    validate_tools([{"type": "function", "function": {
        "name": "get_order",
        "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}},
    }}])  # should not raise

def test_validate_tools_bad_name():
    from open_webui.routers.public.tools_schema import validate_tools
    from open_webui.routers.public.errors import PublicAPIError
    with pytest.raises(PublicAPIError):
        validate_tools([{"type": "function", "function": {"name": "bad name!"}}])

def test_validate_tools_too_many():
    from open_webui.routers.public.tools_schema import validate_tools
    from open_webui.routers.public.errors import PublicAPIError
    tools = [{"type": "function", "function": {"name": f"t{i}"}} for i in range(33)]
    with pytest.raises(PublicAPIError):
        validate_tools(tools)

def test_validate_messages_tool_requires_id():
    from open_webui.routers.public.tools_schema import validate_messages
    from open_webui.routers.public.errors import PublicAPIError
    with pytest.raises(PublicAPIError):
        validate_messages([{"role": "tool", "content": "obs"}])

def test_validate_tool_choice_invalid():
    from open_webui.routers.public.tools_schema import validate_tool_choice
    from open_webui.routers.public.errors import PublicAPIError
    with pytest.raises(PublicAPIError):
        validate_tool_choice("sometimes")


# ─── Tool calling: response/message schemas ──────────────────────────────────

def test_chat_message_tool_calls_schema():
    from open_webui.routers.public.schemas import PublicChatMessage, PublicToolCall, PublicToolCallFunction
    msg = PublicChatMessage(
        role="assistant", content=None,
        tool_calls=[PublicToolCall(id="call_001", type="function",
            function=PublicToolCallFunction(name="get_order", arguments='{"order_id":"A123"}'))],
    )
    assert msg.tool_calls[0].function.name == "get_order"

def test_tool_observation_message_schema():
    from open_webui.routers.public.schemas import PublicChatMessage
    msg = PublicChatMessage(role="tool", tool_call_id="call_001", content='{"status":"ok"}')
    assert msg.tool_call_id == "call_001"


# ─── Agent (/agents/run) schemas ─────────────────────────────────────────────

def test_agent_run_request_schema():
    from open_webui.routers.public.schemas import PublicAgentRunRequest, PublicChatMessage
    req = PublicAgentRunRequest(
        model="Qwen/Qwen3.5-2B",
        messages=[PublicChatMessage(role="user", content="What time is it?")],
        allowed_tools=["get_time"], max_steps=4,
    )
    assert req.mode == "internal_react"
    assert req.allowed_tools == ["get_time"]

def test_agent_run_response_schema():
    from open_webui.routers.public.schemas import PublicAgentRunResponse, PublicAgentToolTraceItem
    resp = PublicAgentRunResponse(
        answer="It is noon.",
        tool_trace=[PublicAgentToolTraceItem(tool_name="get_time", arguments={}, status="success")],
        steps=2, finish_reason="stop",
    )
    assert resp.answer == "It is noon."
    assert resp.tool_trace[0].tool_name == "get_time"


# ─── Registry / reasoning suppression ────────────────────────────────────────

def test_tool_registry_examples():
    from open_webui.routers.public.agent.tool_registry import available_tool_names, get_tool_schemas
    names = available_tool_names()
    assert "get_time" in names and "echo" in names
    schemas = get_tool_schemas(["get_time"])
    assert schemas[0]["function"]["name"] == "get_time"

def test_strip_reasoning():
    from open_webui.routers.public.vllm_client import strip_reasoning
    assert strip_reasoning("<think>secret</think>Hello") == "Hello"
    assert strip_reasoning("Hello") == "Hello"


# ─── Tool-call reconciliation (leaked XML + finish_reason) ───────────────────

def test_extract_leaked_tool_calls_qwen_function_tag():
    from open_webui.routers.public.vllm_client import extract_leaked_tool_calls
    content = (
        "<tool_call>\n<function=list_cards>\n"
        "<parameter=nam>2024</parameter>\n</function>\n</tool_call>"
    )
    cleaned, calls = extract_leaked_tool_calls(content)
    assert cleaned is None  # nothing left but the XML
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "list_cards"
    assert '"nam": "2024"' in calls[0]["function"]["arguments"]

def test_extract_leaked_tool_calls_hermes_json():
    from open_webui.routers.public.vllm_client import extract_leaked_tool_calls
    content = 'Here:<tool_call>{"name": "query_card", "arguments": {"id": 7}}</tool_call>'
    cleaned, calls = extract_leaked_tool_calls(content)
    assert cleaned == "Here:"
    assert calls[0]["function"]["name"] == "query_card"

def test_extract_leaked_tool_calls_none():
    from open_webui.routers.public.vllm_client import extract_leaked_tool_calls
    cleaned, calls = extract_leaked_tool_calls("just a normal answer")
    assert calls == []
    assert cleaned == "just a normal answer"

def test_reconcile_recovers_xml_and_sets_finish_reason():
    from open_webui.routers.public.vllm_client import reconcile_completion
    data = {"choices": [{
        "finish_reason": "stop",
        "message": {"role": "assistant",
                    "content": "<tool_call>{\"name\": \"f\", \"arguments\": {}}</tool_call>"},
    }]}
    reconcile_completion(data)
    choice = data["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["tool_calls"][0]["function"]["name"] == "f"

def test_reconcile_none_mode_strips_xml_without_tool_calls():
    # tool_choice='none' / chat mode: leaked XML must be stripped but NOT promoted
    # to tool_calls (client asked for no tool calling).
    from open_webui.routers.public.vllm_client import reconcile_completion
    data = {"choices": [{
        "finish_reason": "stop",
        "message": {"role": "assistant",
                    "content": "<tool_call>\n<function=get_weather>\n"
                               "<parameter=city>Hà Nội</parameter>\n</function>\n</tool_call>"},
    }]}
    reconcile_completion(data, allow_tool_calls=False)
    choice = data["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert not choice["message"].get("tool_calls")
    assert "<tool_call>" not in (choice["message"].get("content") or "")

def test_reconcile_downgrades_empty_tool_calls():
    from open_webui.routers.public.vllm_client import reconcile_completion
    data = {"choices": [{
        "finish_reason": "tool_calls",
        "message": {"role": "assistant", "content": "Hello", "tool_calls": None},
    }]}
    reconcile_completion(data)
    choice = data["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert "tool_calls" not in choice["message"]


# ─── Streaming reasoning filter (split <think> across chunks) ────────────────

def test_stream_filter_split_think_tag():
    from open_webui.routers.public.vllm_client import _ReasoningStreamFilter
    f = _ReasoningStreamFilter()
    out = "".join([f.feed("Ans"), f.feed("wer <thi"), f.feed("nk>secret"),
                   f.feed(" stuff</thi"), f.feed("nk> done"), f.flush()])
    assert "secret" not in out and "<think>" not in out
    assert out == "Answer  done"

def test_stream_filter_plain_text():
    from open_webui.routers.public.vllm_client import _ReasoningStreamFilter
    f = _ReasoningStreamFilter()
    out = f.feed("Hello world") + f.flush()
    assert out == "Hello world"


# ─── Argument coercion + slug normalization ──────────────────────────────────

def test_coerce_arguments_normalizes_accented_key_and_type():
    from open_webui.routers.public.agent.tool_executor import coerce_arguments
    schema = {"type": "object", "properties": {
        "nam": {"type": "integer"}, "tinh_thanh": {"type": "string"}}}
    out = coerce_arguments({"năm": "2023", "tinh_thanh": "TP.HCM"}, schema)
    assert out == {"nam": 2023, "tinh_thanh": "TP.HCM"}

def test_coerce_arguments_passthrough_unknown():
    from open_webui.routers.public.agent.tool_executor import coerce_arguments
    schema = {"type": "object", "properties": {"nam": {"type": "integer"}}}
    out = coerce_arguments({"unknown_key": "x"}, schema)
    assert out == {"unknown_key": "x"}


# ─── tool_choice cross-checks against tools ──────────────────────────────────

def test_validate_tool_choice_named_must_exist():
    from open_webui.routers.public.tools_schema import validate_tool_choice
    from open_webui.routers.public.errors import PublicAPIError
    with pytest.raises(PublicAPIError):
        validate_tool_choice(
            {"type": "function", "function": {"name": "missing"}},
            tool_names={"present"},
        )

def test_validate_tool_choice_required_needs_tools():
    from open_webui.routers.public.tools_schema import validate_tool_choice
    from open_webui.routers.public.errors import PublicAPIError
    with pytest.raises(PublicAPIError):
        validate_tool_choice("required", tool_names=set())

def test_validate_tool_choice_named_ok():
    from open_webui.routers.public.tools_schema import validate_tool_choice
    validate_tool_choice(
        {"type": "function", "function": {"name": "present"}},
        tool_names={"present"},
    )  # should not raise


# ─── Intent router ────────────────────────────────────────────────────────────

def _route(text):
    from open_webui.routers.public.agent.intent_router import route_intent
    return route_intent([{"role": "user", "content": text}])

def test_route_general_qa_no_tools():
    r = _route("Bộ Y tế thành lập năm nào?")
    # "năm nào" is a general phrasing; but a 4-digit year would flip to data —
    # this question has none, so it should be general and suppress tools.
    assert r["category"] == "general_qa"
    assert r["suggested_tool_choice"] == "none"

def test_route_data_query():
    r = _route("Cho tôi số liệu giường bệnh Hà Nội năm 2024")
    assert r["category"] == "data_query"
    assert r["suggested_tool_choice"] == "auto"

def test_route_policy_query():
    r = _route("Quy định giường bệnh tối thiểu theo thông tư là gì?")
    assert r["category"] == "policy_query"
    assert r["suggested_tool_choice"] == "auto"

def test_route_mixed():
    r = _route("Số liệu giường bệnh Hà Nội 2024 và đánh giá rủi ro theo quy định")
    assert r["category"] == "mixed"

def test_route_default_tool_task():
    r = _route("Giúp tôi việc này")
    assert r["category"] == "tool_task"
    assert r["suggested_tool_choice"] == "auto"


# ─── Grounding guard ──────────────────────────────────────────────────────────

def test_grounding_ungrounded_numbers():
    from open_webui.routers.public.grounding import find_ungrounded_numbers
    corpus = "| Hà Nội | 1500 | 2024 |"
    # 1500 and 2024 are grounded; 150000 and 15 (well, 15 has 2 digits) are invented.
    assert find_ungrounded_numbers("Hà Nội có 1500 ca năm 2024", corpus) == []
    assert "150000" in find_ungrounded_numbers("dân số 150.000 người", corpus)

def test_grounding_thousand_separator_matches():
    from open_webui.routers.public.grounding import find_ungrounded_numbers
    # 1.500 in answer should match 1500 in corpus (separator-normalized).
    assert find_ungrounded_numbers("khoảng 1.500 ca", "tổng 1500") == []

def test_grounding_ignores_alphanumeric_ids():
    from open_webui.routers.public.grounding import find_ungrounded_numbers
    # "19" inside "COVID-19" must NOT be flagged as an ungrounded data number.
    assert find_ungrounded_numbers("liên quan đến COVID-19 và dịch bệnh", "") == []

def test_grounding_foreign_script():
    from open_webui.routers.public.grounding import contains_foreign_script
    assert contains_foreign_script("病床數量 vừa phải") is True
    assert contains_foreign_script("số giường bệnh vừa phải") is False

def test_grounding_report_ok():
    from open_webui.routers.public.grounding import grounding_report
    r = grounding_report("Hà Nội 1500 ca", "1500")
    assert r["ok"] is True and r["ungrounded_numbers"] == [] and r["foreign_script"] is False


def test_model_alias_display_to_internal():
    from open_webui.routers.public.model_alias import (
        DISPLAY_MODEL_NAME,
        INTERNAL_MODEL_NAME,
        to_internal_id,
    )
    assert to_internal_id(DISPLAY_MODEL_NAME) == INTERNAL_MODEL_NAME
    assert to_internal_id(INTERNAL_MODEL_NAME) == INTERNAL_MODEL_NAME
    assert to_internal_id("other-model") == "other-model"

def test_model_alias_candidates_cover_both_names():
    from open_webui.routers.public.model_alias import (
        DISPLAY_MODEL_NAME,
        INTERNAL_MODEL_NAME,
        alias_candidates,
    )
    both = {DISPLAY_MODEL_NAME, INTERNAL_MODEL_NAME}
    # Either name must match a registry that only knows one of them.
    assert alias_candidates(DISPLAY_MODEL_NAME) == both
    assert alias_candidates(INTERNAL_MODEL_NAME) == both
    assert alias_candidates("other-model") == {"other-model"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
