"""
Intent router for the internal ReAct agent (/agents/run).

A deterministic, fail-safe pre-pass that classifies the user's request BEFORE the
ReAct loop, so the agent does not:
  - call data tools for general-knowledge questions (e.g. "Bộ Y tế thành lập năm nào?")
  - answer policy/regulation questions from parametric memory instead of looking them up

It returns a category, a guidance string to inject into the system prompt, and a
suggested tool_choice. The router is intentionally CONSERVATIVE: it only suppresses
tools (GENERAL_QA -> tool_choice "none") when there are clear general-fact signals AND
no data/policy signals. When unsure it keeps tools enabled ("auto"), so a
misclassification never silently denies the agent the tools it needs.

Pure functions only — no I/O, no model calls — so it is cheap and unit-testable.
"""

import re
from typing import Optional

# ─── Categories ───────────────────────────────────────────────────────────────

GENERAL_QA = "general_qa"      # encyclopedic fact; no internal data needed
DATA_QUERY = "data_query"      # needs internal data tools
POLICY_QUERY = "policy_query"  # needs knowledge/regulation lookup
MIXED = "mixed"                # both data and policy
TOOL_TASK = "tool_task"        # default: let the model decide (tools enabled)

# ─── Signal keywords (Vietnamese business domain) ─────────────────────────────

_POLICY_SIGNALS = [
    "quy định", "quy chế", "chính sách", "tiêu chuẩn", "định mức", "tối thiểu",
    "tối đa", "theo luật", "theo quy định", "thông tư", "nghị định", "quyết định số",
    "điều kiện", "được phép", "có được", "yêu cầu pháp lý", "căn cứ pháp lý",
    "đánh giá rủi ro", "rủi ro", "tuân thủ", "bắt buộc",
]

_DATA_SIGNALS = [
    "số liệu", "thống kê", "bao nhiêu", "số lượng", "tổng số", "trung bình",
    "tỉ lệ", "tỷ lệ", "biểu đồ", "dữ liệu", "truy vấn", "card", "tỉnh", "thành phố",
    "so với năm", "theo năm", "theo tỉnh", "danh sách",
]

# General-fact phrasings (factual, encyclopedic).
_GENERAL_SIGNALS = [
    "là gì", "là ai", "nghĩa là gì", "viết tắt của", "thành lập năm nào",
    "ra đời năm nào", "ai là", "ở đâu", "khi nào", "định nghĩa",
]

# A 4-digit year like 2023/2024 strongly implies a data query.
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _last_user_text(messages: list) -> str:
    for msg in reversed(messages):
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
        if role == "user":
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        return part.get("text", "")
    return ""


def _has_any(text: str, keywords: list) -> bool:
    return any(kw in text for kw in keywords)


# ─── Guidance ─────────────────────────────────────────────────────────────────

_GUIDANCE = {
    GENERAL_QA: (
        "Phân loại: câu hỏi kiến thức chung, KHÔNG cần dữ liệu nội bộ. "
        "Trả lời trực tiếp và ngắn gọn; không gọi bất kỳ tool nào."
    ),
    DATA_QUERY: (
        "Phân loại: câu hỏi cần DỮ LIỆU nội bộ. Dùng các tool truy vấn dữ liệu theo đúng "
        "thứ tự (liệt kê nguồn → lấy tham số → truy vấn). Khi tạo filter, chỉ dùng slug "
        "không dấu đúng schema của tool (ví dụ 'nam', 'tinh_thanh'), không dùng tên có dấu."
    ),
    POLICY_QUERY: (
        "Phân loại: câu hỏi về QUY ĐỊNH/CHÍNH SÁCH. Bắt buộc tra cứu tri thức "
        "(ví dụ search_knowledge) trước khi trả lời; tuyệt đối không tự suy diễn quy định "
        "từ trí nhớ. Nếu không tìm thấy căn cứ, nói rõ là không đủ căn cứ."
    ),
    MIXED: (
        "Phân loại: câu hỏi vừa cần DỮ LIỆU vừa cần QUY ĐỊNH. Hãy truy vấn dữ liệu để lấy "
        "số liệu VÀ tra cứu tri thức (search_knowledge) để lấy căn cứ quy định, rồi mới "
        "tổng hợp. Chỉ dùng số liệu/căn cứ có trong observation."
    ),
    TOOL_TASK: (
        "Dùng tool khi chúng giúp trả lời; nếu câu hỏi không cần dữ liệu nội bộ thì trả "
        "lời trực tiếp."
    ),
}


# ─── Router ──────────────────────────────────────────────────────────────────

def route_intent(messages: list, available_tools: Optional[list] = None) -> dict:
    """Classify the request. Returns {category, guidance, suggested_tool_choice, reason}.

    suggested_tool_choice is "none" only for confident GENERAL_QA; otherwise "auto".
    """
    text = _last_user_text(messages).strip().lower()

    has_policy = _has_any(text, _POLICY_SIGNALS)
    has_data = _has_any(text, _DATA_SIGNALS) or bool(_YEAR_RE.search(text))
    has_general = _has_any(text, _GENERAL_SIGNALS)

    if has_policy and has_data:
        category, reason = MIXED, "policy+data signals"
    elif has_policy:
        category, reason = POLICY_QUERY, "policy signals"
    elif has_data:
        category, reason = DATA_QUERY, "data signals"
    elif has_general:
        # Confident general fact: general phrasing AND no data/policy signals.
        category, reason = GENERAL_QA, "general-fact phrasing, no data/policy signals"
    else:
        category, reason = TOOL_TASK, "no strong signals; defer to model"

    suggested_tool_choice = "none" if category == GENERAL_QA else "auto"

    return {
        "category": category,
        "guidance": _GUIDANCE[category],
        "suggested_tool_choice": suggested_tool_choice,
        "reason": reason,
    }
