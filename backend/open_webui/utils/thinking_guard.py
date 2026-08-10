"""
Qwen Thinking Guard — Middleware for Open WebUI ↔ Ollama

Intercepts Ollama /api/chat payloads inside Open WebUI to:
1. Classify user intent (FAST_CHAT / DIRECT_TASK / THINKING_TASK)
2. Inject `think: false` and a strict system prompt for simple queries
3. Prevent Qwen3.5 from entering thinking mode for daily conversation

This module is imported and called from ollama.py's generate_chat_completion.
It does NOT change any other Open WebUI logic.
"""

import re
import logging
import copy
from typing import Optional

log = logging.getLogger(__name__)

# ─── Mode Constants ──────────────────────────────────────────────────────────

MODE_FAST_CHAT = "FAST_CHAT"
MODE_DIRECT_TASK = "DIRECT_TASK"
MODE_THINKING_TASK = "THINKING_TASK"

# ─── Pattern Matching ────────────────────────────────────────────────────────

DAILY_CONVERSATION_PATTERNS = [
    r"^(hi|hello|hey|xin chào|chào|chào bạn|alo|ok|okay|thanks|cảm ơn|thank you|bye|tạm biệt|good|great)\s*[!.?]*$",
    r"^(good morning|good afternoon|good evening|chào buổi sáng|chào buổi tối)\s*[!.?]*$",
    r"^bạn là ai\s*[!.?]*$",
    r"^bạn khỏe không\s*[!.?]*$",
    r"^bạn tên (gì|là gì)\s*[!.?]*$",
    r"^hôm nay thế nào",
    r"^kể chuyện vui",
    r"^bạn có thể giúp gì",
    r"^mình cần giúp",
]

TRANSLATION_REWRITE_KEYWORDS = [
    "dịch", "translate", "viết lại", "rewrite", "rút gọn", "tóm tắt",
    "sửa câu", "sửa prompt", "đặt tên", "viết email", "tạo câu hỏi",
]

SIMPLE_KNOWLEDGE_PATTERNS = [
    r".*\blà gì\s*\??$",
]

SIMPLE_KNOWLEDGE_KEYWORDS = [
    "lệnh xem log", "lệnh xóa", "cách chạy model", "cài ",
]

COMPLEX_TASK_KEYWORDS = [
    "thuật toán", "tối ưu o(n)", "độ phức tạp", "thiết kế kiến trúc",
    "phân tích tài liệu", "phân tích nguyên nhân", "chứng minh",
    "debug toàn bộ", "kiểm tra kiến trúc",
]

# ─── System Prompts ──────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    MODE_FAST_CHAT: (
        "You are a fast daily conversation assistant.\n\n"
        "Rules:\n"
        "- Answer immediately.\n"
        "- Do not think.\n"
        "- Do not analyze.\n"
        "- Do not plan.\n"
        "- Do not output <think>.\n"
        "- Do not reveal hidden reasoning.\n"
        "- For greetings, thanks, and small talk, answer naturally in 1-3 short sentences.\n"
        "- Answer in the same language as the user."
    ),
    MODE_DIRECT_TASK: (
        "You are a direct task assistant.\n\n"
        "Rules:\n"
        "- Answer directly and practically.\n"
        "- Do not output <think>.\n"
        "- Do not reveal chain-of-thought.\n"
        "- Do not write internal planning.\n"
        "- If the task is simple, produce the final answer immediately.\n"
        "- Use the same language as the user."
    ),
    MODE_THINKING_TASK: (
        "You are a technical assistant.\n\n"
        "Rules:\n"
        "- You may reason internally only when needed.\n"
        "- Never reveal chain-of-thought.\n"
        "- Never output <think> or hidden reasoning.\n"
        "- Return only the final useful answer, code, explanation, or steps.\n"
        "- Use the same language as the user."
    ),
}


# ─── Classifier ──────────────────────────────────────────────────────────────

def classify_intent(user_message: str) -> dict:
    """
    Fast rule-based intent classification.
    Returns {"mode": str, "allow_thinking": bool, "reason": str}
    """
    # Ép 100% sử dụng chế độ Thinking, nhưng prompt của THINKING_TASK đã giấu thẻ <think>
    return {"mode": MODE_THINKING_TASK, "allow_thinking": True, "reason": "force_all_thinking_hidden"}


# ─── Payload Transformer ────────────────────────────────────────────────────

def apply_thinking_guard(payload: dict) -> dict:
    """
    Mutates the Ollama /api/chat payload in-place:
    - Classifies the user's last message
    - Sets `think` field to control Qwen3.5 thinking mode
    - Prepends a mode-appropriate system prompt
    
    Returns the classification dict for logging.
    """
    messages = payload.get("messages", [])
    if not messages:
        return {"mode": MODE_DIRECT_TASK, "allow_thinking": False, "reason": "no_messages"}

    # Find the last user message
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                user_message = content
            elif isinstance(content, list):
                # Multimodal: extract text parts
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        user_message = part.get("text", "")
                        break
            break

    if not user_message:
        return {"mode": MODE_DIRECT_TASK, "allow_thinking": False, "reason": "no_user_message"}

    classification = classify_intent(user_message)
    mode = classification["mode"]
    allow_thinking = classification["allow_thinking"]

    # Set the `think` field on the payload
    # This tells Ollama/Qwen3.5 whether to use thinking mode
    payload["think"] = allow_thinking

    # Prepend system prompt based on mode
    system_prompt = SYSTEM_PROMPTS[mode]

    # Check if there's already a system message
    if messages and messages[0].get("role") == "system":
        # Prepend our guard prompt to existing system message
        existing = messages[0].get("content", "")
        messages[0]["content"] = system_prompt + "\n\n" + existing
    else:
        # Insert new system message at position 0
        messages.insert(0, {"role": "system", "content": system_prompt})

    payload["messages"] = messages

    log.info(
        f"[ThinkingGuard] user_message_length={len(user_message)} | "
        f"word_count={len(user_message.split())} | "
        f"detected_mode={mode} | "
        f"allow_thinking={allow_thinking} | "
        f"reason={classification['reason']}"
    )

    return classification
