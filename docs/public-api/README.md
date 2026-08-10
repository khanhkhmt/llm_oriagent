# OriAgent Public API — Tài liệu dành cho Developer

> **Phiên bản:** v1  
> **Base URL:** `https://llm.oriagent.com/api/public/v1`  
> **Tương thích:** OpenAI Chat Completions API

---

## Mục lục

1. [Overview](#1-overview)
2. [Base URL & Authentication](#2-base-url--authentication)
3. [Endpoint chính: Chat Completions](#3-endpoint-chính-chat-completions)
4. [Case 1 — Chat bình thường](#4-case-1--chat-bình-thường)
5. [Case 2 — External Tool Calling](#5-case-2--external-tool-calling)
6. [Case 3 — Gửi Observation / Tool Result lại model](#6-case-3--gửi-observation--tool-result-lại-model)
7. [Case 4 — Internal ReAct Agent (/agents/run)](#7-case-4--internal-react-agent-agentsrun)
8. [Request Classification Rules](#8-request-classification-rules)
9. [Tool Schema Reference](#9-tool-schema-reference)
10. [Python OpenAI SDK Examples](#10-python-openai-sdk-examples)
11. [JavaScript / TypeScript Examples](#11-javascript--typescript-examples)
12. [Streaming](#12-streaming)
13. [Error Handling](#13-error-handling)
14. [Rate Limits](#14-rate-limits)
15. [Security Notes](#15-security-notes)
16. [Best Practices](#16-best-practices)
17. [vLLM Backend Notes](#17-vllm-backend-notes)
18. [Checklist nhanh](#18-checklist-nhanh)

---

## 1. Overview

**OriAgent Public API** cho phép hệ thống bên thứ ba gọi model LLM thông qua HTTP API chuẩn OpenAI. Backend inference được chạy bằng **vLLM** với OpenAI-compatible server.

API hỗ trợ ba loại use case chính:

| Use case | Endpoint | Mô tả |
|----------|----------|-------|
| Chat bình thường | `POST /chat/completions` | Hỏi đáp không cần tool |
| External tool calling | `POST /chat/completions` | Model chọn tool, **bên thứ ba tự execute** |
| Internal ReAct Agent | `POST /agents/run` | Hệ thống OriAgent tự chạy agent loop nội bộ |

### Luồng xử lý — Chat thường

```
Client / Backend bên thứ ba
  → POST /chat/completions
  → OriAgent Public API
  → vLLM Server
  → OriAgent Public API
  → Trả response về Client
```

### Luồng xử lý — External Tool Calling

> **Quan trọng:** API của OriAgent **không tự execute tool** của bên thứ ba.  
> Model chỉ sinh ra `tool_calls`. Bên thứ ba nhận về và **tự execute tool**.

```
Third-party ReAct Agent
  → Gửi messages + tools
  → POST /chat/completions
  → vLLM sinh tool_calls
  → API trả tool_calls về Third-party
  → Third-party tự execute tool → nhận Observation
  → Gửi lại Observation qua role="tool"
  → POST /chat/completions
  → vLLM đọc Observation, trả final answer
  → Third-party nhận final answer
```

### Điểm khác biệt quan trọng

| | `/chat/completions` | `/agents/run` |
|--|--|--|
| Execute external tool | ❌ Không | N/A |
| Execute internal tool | ❌ Không | ✅ Có |
| Expose Thought/Reasoning | ❌ Không | ❌ Không |
| Ai chạy ReAct loop | Bên thứ ba tự chạy | OriAgent chạy nội bộ |

> **Chú ý về thuật ngữ:** ReAct ở đây là **agent loop**: `Thought → Action → Observation → Final Answer`, không liên quan đến React.js.

---

## 2. Base URL & Authentication

### Base URL

```
https://llm.oriagent.com/api/public/v1
```

### Authentication

Tất cả request (trừ `/health`) đều phải có header:

```
Authorization: Bearer YOUR_API_KEY
```

Lấy API key tại: **OriAgent → Cài đặt → API Keys → Tạo key mới**

### Ví dụ curl

```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:2b",
    "messages": [
      {
        "role": "user",
        "content": "Xin chào"
      }
    ]
  }'
```

### Lưu ý bảo mật

- **Không** gọi API trực tiếp từ frontend/browser — API key sẽ bị lộ.
- Nên gọi API từ **backend server** của bên thứ ba.
- API key phải được lưu trong biến môi trường, không hardcode trong source code.

---

## 3. Endpoint chính: Chat Completions

```
POST https://llm.oriagent.com/api/public/v1/chat/completions
```

### Request Body

```json
{
  "model": "qwen3.5:2b",
  "messages": [],
  "tools": [],
  "tool_choice": "auto",
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false,
  "mode": "chat"
}
```

### Mô tả các field

| Field | Type | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `model` | string | ✅ | Tên model cần gọi, ví dụ `"qwen3.5:2b"` |
| `messages` | array | ✅ | Danh sách tin nhắn hội thoại (tối thiểu 1 phần tử) |
| `tools` | array | ❌ | Danh sách tool theo OpenAI function schema (tối đa 32) |
| `tool_choice` | string/object | ❌ | Cách model chọn tool (xem bảng bên dưới) |
| `temperature` | float | ❌ | Độ sáng tạo, từ `0.0` đến `2.0` (mặc định `0.7`) |
| `max_tokens` | integer | ❌ | Giới hạn số token sinh ra (mặc định không giới hạn) |
| `stream` | boolean | ❌ | `true` để nhận SSE streaming, mặc định `false` |
| `mode` | string | ❌ | `"chat"` hoặc `"external_tool_calling"` — tự suy luận nếu bỏ trống |

### Các giá trị `tool_choice`

| Giá trị | Ý nghĩa |
|---------|---------|
| `"none"` | Model không được gọi tool |
| `"auto"` | Model tự quyết định có gọi tool hay không |
| `"required"` | Model bắt buộc phải gọi ít nhất một tool |
| `{"type":"function","function":{"name":"tên_tool"}}` | Ép model gọi đúng tool đó |

### Cấu trúc `messages`

Mỗi phần tử trong `messages` có thể là:

```json
// Tin nhắn người dùng
{"role": "user", "content": "Nội dung câu hỏi"}

// Tin nhắn hệ thống
{"role": "system", "content": "Bạn là trợ lý hỗ trợ khách hàng."}

// Tin nhắn assistant (chat thường)
{"role": "assistant", "content": "Nội dung trả lời"}

// Tin nhắn assistant khi model gọi tool
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_001",
      "type": "function",
      "function": {
        "name": "get_order",
        "arguments": "{\"order_id\": \"A123\"}"
      }
    }
  ]
}

// Tin nhắn Observation từ tool (bên thứ ba gửi lại)
{
  "role": "tool",
  "tool_call_id": "call_001",
  "content": "{\"status\": \"Đang giao\", \"total\": 250000}"
}
```

---

## 4. Case 1 — Chat bình thường

Dùng khi client chỉ cần hỏi đáp, **không cần tool**.

### Request

```json
{
  "model": "qwen3.5:2b",
  "mode": "chat",
  "messages": [
    {
      "role": "user",
      "content": "API public là gì?"
    }
  ],
  "stream": false
}
```

### Luồng xử lý

```
1. Client gửi câu hỏi
2. API nhận request, phát hiện không có tools
3. API gọi vLLM với payload đã chuẩn bị
4. vLLM trả final answer
5. API trả kết quả về client
```

### Response

```json
{
  "id": "chatcmpl_abc123",
  "object": "chat.completion",
  "created": 1748750000,
  "model": "qwen3.5:2b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "API public là API được mở ra để hệ thống bên ngoài có thể gọi và sử dụng chức năng của hệ thống bạn thông qua HTTP request."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 18,
    "completion_tokens": 42,
    "total_tokens": 60
  }
}
```

### curl

```bash
curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:2b",
    "mode": "chat",
    "messages": [
      {"role": "user", "content": "API public là gì?"}
    ]
  }'
```

> **Ghi chú:**
> - Không truyền `tools` khi chỉ cần chat thường.
> - `tool_choice` mặc định là `"none"` trong chế độ `chat`.
> - API không khởi động ReAct loop trong case này.

---

## 5. Case 2 — External Tool Calling

Dùng khi bên thứ ba có **ReAct Agent riêng** và muốn model chọn tool để gọi.

> **Quan trọng:**
> - API của OriAgent **không execute tool** của bên thứ ba.
> - API chỉ trả `tool_calls` — danh sách tool model muốn gọi kèm arguments.
> - **Bên thứ ba tự execute tool** và gửi kết quả lại qua `role="tool"`.

### Lượt 1 — Gửi request kèm tools

#### Request

```json
{
  "model": "qwen3.5:2b",
  "mode": "external_tool_calling",
  "messages": [
    {
      "role": "user",
      "content": "Kiểm tra đơn hàng A123 giúp tôi"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_order",
        "description": "Lấy thông tin đơn hàng theo mã đơn hàng",
        "parameters": {
          "type": "object",
          "properties": {
            "order_id": {
              "type": "string",
              "description": "Mã đơn hàng"
            }
          },
          "required": ["order_id"]
        }
      }
    }
  ],
  "tool_choice": "auto",
  "stream": false
}
```

#### Luồng xử lý — Lượt 1

```
1. Bên thứ ba gửi messages + tools
2. API validate tools schema
3. API forward request sang vLLM
4. vLLM quyết định cần gọi get_order
5. vLLM sinh tool_calls
6. API trả tool_calls về bên thứ ba
7. API KHÔNG tự gọi get_order
```

#### Response — Lượt 1

```json
{
  "id": "chatcmpl_abc123",
  "object": "chat.completion",
  "created": 1748750000,
  "model": "qwen3.5:2b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_001",
            "type": "function",
            "function": {
              "name": "get_order",
              "arguments": "{\"order_id\":\"A123\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

#### Giải thích response

| Field | Ý nghĩa |
|-------|---------|
| `choices[0].message.content` | `null` — model chưa trả lời, cần execute tool trước |
| `choices[0].message.tool_calls` | Danh sách tool model muốn gọi |
| `tool_calls[0].id` | ID duy nhất của tool call, dùng để gắn Observation sau |
| `tool_calls[0].function.name` | Tên tool cần gọi |
| `tool_calls[0].function.arguments` | JSON string chứa tham số — bên thứ ba phải `JSON.parse` trước khi dùng |
| `finish_reason` | `"tool_calls"` — báo hiệu cần execute tool, chưa có final answer |

> Bên thứ ba cần:
> 1. Parse `arguments` từ JSON string.
> 2. Gọi hàm `get_order` với `order_id = "A123"` trong hệ thống của mình.
> 3. Gửi kết quả lại API theo định dạng `role="tool"`.

---

## 6. Case 3 — Gửi Observation / Tool Result lại model

Sau khi bên thứ ba execute tool, cần gửi kết quả (Observation) lại API để model tạo **final answer**.

> Đây là **lượt 2** trong vòng lặp ReAct. Bên thứ ba tự quản lý vòng lặp này.

### Ví dụ: Bên thứ ba đã gọi `get_order("A123")` và nhận kết quả

```json
{
  "order_id": "A123",
  "status": "Đang giao",
  "total": 250000,
  "estimated_delivery": "2026-06-03"
}
```

### Lượt 2 — Gửi Observation lại API

#### Request

```json
{
  "model": "qwen3.5:2b",
  "mode": "external_tool_calling",
  "messages": [
    {
      "role": "user",
      "content": "Kiểm tra đơn hàng A123 giúp tôi"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_001",
          "type": "function",
          "function": {
            "name": "get_order",
            "arguments": "{\"order_id\":\"A123\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_001",
      "content": "{\"order_id\":\"A123\",\"status\":\"Đang giao\",\"total\":250000,\"estimated_delivery\":\"2026-06-03\"}"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_order",
        "description": "Lấy thông tin đơn hàng theo mã đơn hàng",
        "parameters": {
          "type": "object",
          "properties": {
            "order_id": {"type": "string"}
          },
          "required": ["order_id"]
        }
      }
    }
  ],
  "tool_choice": "auto",
  "stream": false
}
```

#### Luồng xử lý — Lượt 2

```
1. Bên thứ ba gửi lại đầy đủ conversation history
2. Messages gồm: user → assistant(tool_calls) → tool(Observation)
3. API forward sang vLLM
4. vLLM đọc Observation từ role="tool"
5. vLLM tổng hợp và trả final answer
6. API trả final answer về bên thứ ba
```

#### Response — Final Answer

```json
{
  "id": "chatcmpl_def456",
  "object": "chat.completion",
  "created": 1748750010,
  "model": "qwen3.5:2b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Đơn hàng A123 hiện đang được giao, tổng giá trị là 250.000đ và dự kiến giao vào ngày 03/06/2026."
      },
      "finish_reason": "stop"
    }
  ]
}
```

> **Quy tắc bắt buộc khi gửi Observation:**
> - `role="tool"` **bắt buộc** phải có trường `tool_call_id`.
> - `tool_call_id` phải khớp chính xác với `id` trong `tool_calls` của lượt trước.
> - `content` của `role="tool"` nên là **JSON string** (không phải object).
> - Phải gửi lại **nguyên vẹn** message `assistant` chứa `tool_calls` — không được xóa hay sửa.

---

## 7. Case 4 — Internal ReAct Agent (/agents/run)

```
POST https://llm.oriagent.com/api/public/v1/agents/run
```

Endpoint này dùng khi client muốn **hệ thống OriAgent tự chạy ReAct Agent nội bộ**, không cần bên thứ ba quản lý vòng lặp.

### Khác biệt so với `/chat/completions`

| | `/chat/completions` | `/agents/run` |
|--|--|--|
| Execute external tool | ❌ Không bao giờ | N/A |
| Execute internal tool | ❌ Không | ✅ Có, theo `allowed_tools` |
| Ai chạy vòng lặp | Bên thứ ba | OriAgent nội bộ |
| Kết quả trả về | `tool_calls` hoặc `content` | `answer` + `tool_trace` |
| Expose Thought/Reasoning | ❌ Không | ❌ Không |

### Internal tools là gì?

Internal tools là các function/API nội bộ mà backend OriAgent sở hữu và có quyền gọi, ví dụ:

- `search_docs` — tìm kiếm tài liệu nội bộ
- `search_vector_db` — truy vấn vector database
- `read_database` — đọc dữ liệu từ database (read-only)
- `get_model_status` — kiểm tra trạng thái model
- `get_api_key_usage` — xem thống kê sử dụng API key

### Request

```json
{
  "model": "qwen3.5:2b",
  "mode": "internal_react",
  "messages": [
    {
      "role": "user",
      "content": "Tìm tài liệu liên quan đến API public của tôi"
    }
  ],
  "allowed_tools": [
    "search_docs",
    "search_vector_db"
  ],
  "max_steps": 5,
  "stream": false
}
```

| Field | Type | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `model` | string | ✅ | Model ID |
| `messages` | array | ✅ | Conversation (thường chỉ 1 tin user) |
| `allowed_tools` | string[] | ✅ | Danh sách internal tool được phép dùng trong run này |
| `max_steps` | integer | ❌ | Số bước ReAct tối đa, mặc định 5, tối đa 8 |
| `temperature` | float | ❌ | Độ sáng tạo mỗi lần gọi model |
| `max_tokens` | integer | ❌ | Giới hạn token mỗi lần gọi model |

### Luồng xử lý nội bộ

```
Client gọi POST /agents/run
  ↓
OriAgent khởi tạo ReAct Agent nội bộ
  ↓
[Vòng lặp — tối đa max_steps lần]
  ↓
Agent gọi vLLM (Thought bên trong, không expose ra ngoài)
  ↓
Nếu model sinh tool_calls:
  → Backend tự execute internal tool
  → Nhận Observation
  → Đưa Observation lại vào vLLM
  → Lặp tiếp
Nếu model trả final answer:
  → Dừng vòng lặp
  ↓
API trả { answer, tool_trace } về client
```

### Response

```json
{
  "answer": "Tài liệu API public của bạn bao gồm các phần: Base URL & Authentication, Chat Completion (chat thường và tool calling), Internal ReAct Agent (/agents/run), Error Handling và Best Practices.",
  "tool_trace": [
    {
      "tool_name": "search_docs",
      "arguments": {
        "query": "API public documentation"
      },
      "status": "success"
    }
  ],
  "steps": 2,
  "finish_reason": "stop"
}
```

| Field | Mô tả |
|-------|-------|
| `answer` | Final answer — không chứa Thought hay reasoning nội bộ |
| `tool_trace` | Danh sách tool đã được execute, chỉ chứa thông tin an toàn |
| `steps` | Số bước ReAct đã thực hiện |
| `finish_reason` | `"stop"` (hoàn thành) hoặc `"max_steps"` (đã đạt giới hạn) |

> **Ghi chú bảo mật:**
> - `tool_trace` chỉ chứa thông tin an toàn (tên tool, arguments công khai, status).
> - Không trả full Thought hay reasoning nội bộ.
> - `allowed_tools` chỉ có thể chứa internal tools đã được đăng ký trong hệ thống.
> - Client không thể gọi internal tool tùy ý nếu không được cấp quyền.

---

## 8. Request Classification Rules

API tự động phân loại request theo logic sau khi không truyền `mode` tường minh:

```python
def classify_request(req):
    # 1. Mode tường minh — ưu tiên cao nhất
    if req.mode:
        return req.mode

    # 2. Có tools → external tool calling
    if req.tools:
        return "external_tool_calling"

    # 3. tool_choice khác "none" → external tool calling
    if req.tool_choice and req.tool_choice != "none":
        return "external_tool_calling"

    # 4. Có role="tool" trong messages → đang ở giữa tool calling loop
    for msg in req.messages:
        if msg.role == "tool":
            return "external_tool_calling"

    # 5. Mặc định → chat thường
    return "chat"
```

### Nguyên tắc quan trọng

- **Ưu tiên `mode` tường minh** — nếu đã truyền `mode` thì không suy luận thêm.
- **Không phân loại bằng cách đoán nội dung** câu hỏi.
- **Không tự chạy `internal_react`** nếu client không yêu cầu rõ — phải gọi `/agents/run` hoặc `mode="internal_react"`.
- Trong chế độ `chat`, `tools` bị bỏ qua và `tool_choice` bị ép thành `"none"`.

---

## 9. Tool Schema Reference

### Format tool hợp lệ

```json
{
  "type": "function",
  "function": {
    "name": "tool_name",
    "description": "Mô tả ngắn gọn chức năng của tool",
    "parameters": {
      "type": "object",
      "properties": {
        "param_name": {
          "type": "string",
          "description": "Mô tả tham số"
        }
      },
      "required": ["param_name"]
    }
  }
}
```

### Quy tắc đặt tên và schema

| Quy tắc | Chi tiết |
|---------|---------|
| `name` | Chỉ chứa chữ cái, số, dấu gạch dưới — khớp `[a-zA-Z0-9_-]{1,64}` |
| `description` | Ngắn gọn, rõ chức năng, tối đa 4096 ký tự |
| `parameters` | Phải là JSON Schema object hợp lệ |
| `required` | Liệt kê đúng các field bắt buộc |
| Số lượng tools | Tối đa 32 tools mỗi request |
| Không đưa secrets | Không ghi API key, password, token vào description |

### Ví dụ tool tốt

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "Lấy thông tin thời tiết hiện tại theo tên thành phố",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "Tên thành phố, ví dụ: Hà Nội, TP.HCM"
        },
        "unit": {
          "type": "string",
          "enum": ["celsius", "fahrenheit"],
          "description": "Đơn vị nhiệt độ"
        }
      },
      "required": ["city"]
    }
  }
}
```

### Ví dụ tool kém — cần tránh

```json
{
  "type": "function",
  "function": {
    "name": "do stuff",
    "description": "Làm mọi thứ",
    "parameters": {}
  }
}
```

> Lý do tệ: tên có khoảng trắng, description mơ hồ, parameters rỗng — model sẽ không biết khi nào và cách nào gọi tool này.

---

## 10. Python OpenAI SDK Examples

API tương thích hoàn toàn với OpenAI Python SDK — chỉ cần đổi `base_url`.

### Cài đặt

```bash
pip install openai
```

### Khởi tạo client

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://llm.oriagent.com/api/public/v1"
)
```

### Chat bình thường

```python
response = client.chat.completions.create(
    model="qwen3.5:2b",
    messages=[
        {"role": "user", "content": "Xin chào, bạn có thể giúp tôi không?"}
    ]
)

print(response.choices[0].message.content)
```

### Tool calling — Lượt 1

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Lấy thông tin đơn hàng",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Mã đơn hàng"}
                },
                "required": ["order_id"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="qwen3.5:2b",
    messages=[
        {"role": "user", "content": "Kiểm tra đơn hàng A123"}
    ],
    tools=tools,
    tool_choice="auto"
)

message = response.choices[0].message

if message.tool_calls:
    tool_call = message.tool_calls[0]
    print("Tool cần gọi:", tool_call.function.name)
    print("Arguments:", tool_call.function.arguments)
```

### Tool calling — Vòng lặp đầy đủ

```python
import json

def get_order(order_id: str) -> dict:
    # Gọi API nội bộ của bạn
    return {
        "order_id": order_id,
        "status": "Đang giao",
        "total": 250000,
        "estimated_delivery": "2026-06-03"
    }

def run_tool_calling_loop(user_query: str):
    messages = [{"role": "user", "content": user_query}]

    while True:
        response = client.chat.completions.create(
            model="qwen3.5:2b",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        choice = response.choices[0]
        message = choice.message

        # Thêm message assistant vào history
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in (message.tool_calls or [])
            ] or None
        })

        if choice.finish_reason == "tool_calls":
            # Execute tool và gửi Observation
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)

                if tool_call.function.name == "get_order":
                    result = get_order(**args)
                else:
                    result = {"error": "unknown tool"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

        else:
            # Final answer
            print("Kết quả:", message.content)
            break

run_tool_calling_loop("Kiểm tra đơn hàng A123 giúp tôi")
```

---

## 11. JavaScript / TypeScript Examples

### Cài đặt

```bash
npm install openai
```

### Chat bình thường

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "YOUR_API_KEY",
  baseURL: "https://llm.oriagent.com/api/public/v1",
});

const response = await client.chat.completions.create({
  model: "qwen3.5:2b",
  messages: [
    {
      role: "user",
      content: "Xin chào, bạn là ai?",
    },
  ],
});

console.log(response.choices[0].message.content);
```

### Tool calling — Lượt 1

```typescript
const tools: OpenAI.ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "get_order",
      description: "Lấy thông tin đơn hàng",
      parameters: {
        type: "object",
        properties: {
          order_id: {
            type: "string",
            description: "Mã đơn hàng",
          },
        },
        required: ["order_id"],
      },
    },
  },
];

const response = await client.chat.completions.create({
  model: "qwen3.5:2b",
  messages: [
    {
      role: "user",
      content: "Kiểm tra đơn hàng A123",
    },
  ],
  tools,
  tool_choice: "auto",
});

const message = response.choices[0].message;

if (message.tool_calls) {
  const toolCall = message.tool_calls[0];
  console.log("Tool cần gọi:", toolCall.function.name);
  console.log("Arguments:", toolCall.function.arguments);
}
```

### Tool calling — Vòng lặp đầy đủ

```typescript
type Message = OpenAI.ChatCompletionMessageParam;

async function getOrder(orderId: string) {
  // Gọi API nội bộ của bạn
  return {
    order_id: orderId,
    status: "Đang giao",
    total: 250000,
    estimated_delivery: "2026-06-03",
  };
}

async function runToolCallingLoop(userQuery: string) {
  const messages: Message[] = [{ role: "user", content: userQuery }];

  while (true) {
    const response = await client.chat.completions.create({
      model: "qwen3.5:2b",
      messages,
      tools,
      tool_choice: "auto",
    });

    const choice = response.choices[0];
    const message = choice.message;

    messages.push(message);

    if (choice.finish_reason === "tool_calls" && message.tool_calls) {
      for (const toolCall of message.tool_calls) {
        const args = JSON.parse(toolCall.function.arguments);
        let result: unknown;

        if (toolCall.function.name === "get_order") {
          result = await getOrder(args.order_id);
        } else {
          result = { error: "unknown tool" };
        }

        messages.push({
          role: "tool",
          tool_call_id: toolCall.id,
          content: JSON.stringify(result),
        });
      }
    } else {
      console.log("Kết quả:", message.content);
      break;
    }
  }
}

await runToolCallingLoop("Kiểm tra đơn hàng A123 giúp tôi");
```

---

## 12. Streaming

### Bật Streaming

Thêm `"stream": true` vào request body.

```bash
curl -N -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:2b",
    "messages": [
      {"role": "user", "content": "Viết đoạn giới thiệu ngắn về OriAgent"}
    ],
    "stream": true
  }'
```

### Định dạng SSE Response

Response là chuỗi Server-Sent Events (SSE), mỗi dòng có dạng `data: {...}`:

```
data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","choices":[{"delta":{"role":"assistant","content":""},"index":0}]}

data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"OriAgent"},"index":0}]}

data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":" là"},"index":0}]}

data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":" nền tảng"},"index":0}]}

data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","choices":[{"delta":{},"finish_reason":"stop","index":0}]}

data: [DONE]
```

### Python — Streaming

```python
stream = client.chat.completions.create(
    model="qwen3.5:2b",
    messages=[{"role": "user", "content": "Viết đoạn giới thiệu ngắn về OriAgent"}],
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        print(delta.content, end="", flush=True)

print()  # Xuống dòng sau khi xong
```

### JavaScript — Streaming

```typescript
const stream = await client.chat.completions.create({
  model: "qwen3.5:2b",
  messages: [{ role: "user", content: "Viết đoạn giới thiệu ngắn về OriAgent" }],
  stream: true,
});

for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content;
  if (content) process.stdout.write(content);
}
console.log();
```

> **Lưu ý:**
> - `stream=false` trả về response đầy đủ trong một lần.
> - `stream=true` trả về từng chunk qua SSE, kết thúc bằng `data: [DONE]`.
> - vLLM có hỗ trợ streaming `tool_calls` delta nếu model hỗ trợ.

---

## 13. Error Handling

### Định dạng Error Response

```json
{
  "success": false,
  "error": {
    "message": "Mô tả lỗi",
    "type": "invalid_request_error",
    "code": "error_code"
  },
  "request_id": "req_xxx"
}
```

> **Ghi chú:** OpenAI SDK sẽ throw exception khi gặp lỗi HTTP. Hãy bắt exception trong code của bạn.

### Bảng mã lỗi

| HTTP Status | `code` | Mô tả |
|-------------|--------|-------|
| 401 | `missing_api_key` | Không có `Authorization` header |
| 401 | `invalid_api_key` | API key không hợp lệ hoặc đã bị thu hồi |
| 400 | `invalid_model` | Model không tồn tại hoặc không có quyền truy cập |
| 400 | `invalid_messages` | `messages` rỗng hoặc sai định dạng |
| 400 | `invalid_tools_schema` | Tool không đúng format OpenAI function schema |
| 400 | `invalid_tool_choice` | Giá trị `tool_choice` không hợp lệ |
| 400 | `tool_call_id_required` | `role="tool"` thiếu trường `tool_call_id` |
| 400 | `invalid_tool_calls` | Message `assistant` chứa `tool_calls` bị thiếu `id`, `type`, hoặc `function` |
| 400 | `unknown_tool` | `allowed_tools` trong `/agents/run` chứa tool không tồn tại |
| 429 | `rate_limit_exceeded` | Vượt giới hạn request |
| 500 | `internal_server_error` | Lỗi nội bộ phía server |
| 502 | `upstream_error` | vLLM server gặp lỗi |
| 503 | `upstream_error` | vLLM server không khả dụng |

### Ví dụ lỗi thực tế

```json
{
  "success": false,
  "error": {
    "message": "role='tool' requires tool_call_id",
    "type": "invalid_request_error",
    "code": "tool_call_id_required"
  },
  "request_id": "req_abc123"
}
```

```json
{
  "success": false,
  "error": {
    "message": "Tool 'my tool' has invalid name. Only [a-zA-Z0-9_-] allowed.",
    "type": "invalid_request_error",
    "code": "invalid_tools_schema"
  },
  "request_id": "req_abc124"
}
```

### Xử lý lỗi trong Python

```python
from openai import OpenAI, APIStatusError

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://llm.oriagent.com/api/public/v1"
)

try:
    response = client.chat.completions.create(
        model="qwen3.5:2b",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(response.choices[0].message.content)

except APIStatusError as e:
    print(f"HTTP {e.status_code}: {e.message}")
except Exception as e:
    print(f"Lỗi không mong đợi: {e}")
```

### Xử lý lỗi trong JavaScript

```typescript
try {
  const response = await client.chat.completions.create({
    model: "qwen3.5:2b",
    messages: [{ role: "user", content: "Hello" }],
  });
  console.log(response.choices[0].message.content);
} catch (error) {
  if (error instanceof OpenAI.APIError) {
    console.error(`HTTP ${error.status}: ${error.message}`);
  } else {
    console.error("Lỗi không mong đợi:", error);
  }
}
```

---

## 14. Rate Limits

API giới hạn request theo **API key**, cửa sổ trượt 60 giây.

### Giới hạn mặc định

| Endpoint | Giới hạn |
|----------|----------|
| `POST /chat/completions` | 60 request/phút |
| `POST /agents/run` | 20 request/phút |
| `GET /models` | 120 request/phút |
| `POST /audio/transcriptions` | 20 request/phút |
| `POST /audio/speech` | 30 request/phút |
| `POST /images/generations` | 10 request/phút |
| `POST /files` | 30 request/phút |
| `POST /knowledge/query` | 60 request/phút |

### Rate limit response — HTTP 429

```json
{
  "success": false,
  "error": {
    "message": "Rate limit exceeded. Please try again later.",
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded"
  },
  "request_id": "req_xxx"
}
```

### Xử lý Rate Limit trong code

```python
import time

def call_with_retry(messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="qwen3.5:2b",
                messages=messages
            )
        except APIStatusError as e:
            if e.status_code == 429 and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Rate limited. Đợi {wait_time}s trước khi thử lại...")
                time.sleep(wait_time)
            else:
                raise
```

---

## 15. Security Notes

### Dành cho developer bên thứ ba

| ❌ Không nên | ✅ Nên làm |
|-------------|-----------|
| Gọi API trực tiếp từ frontend/browser | Gọi API từ backend server |
| Hardcode API key trong source code | Lưu API key trong biến môi trường |
| Gửi secrets trong `messages` hoặc tool `description` | Chỉ gửi dữ liệu cần thiết |
| Tin tưởng tuyệt đối vào arguments model sinh ra | Luôn validate trước khi execute tool |
| Để model gọi tool ngoài whitelist | Chỉ register và truyền tools đã được kiểm soát |

### Về tool execution

- Với **external tool calling**: bên thứ ba **chịu trách nhiệm hoàn toàn** về việc execute tool.
- Luôn **validate và sanitize** `function.arguments` trước khi dùng — model nhỏ có thể sinh arguments không hợp lệ.
- Không execute tool với quyền admin/root nếu không cần thiết.
- Không để model gọi tool có thể gây side effect nghiêm trọng (xóa dữ liệu, gửi email hàng loạt, v.v.).

### Về nội dung response

- API **không bao giờ** trả Thought/reasoning nội bộ của model ra bên ngoài.
- API **không bao giờ** trả stack trace hay thông tin hệ thống trong error response.
- API **không bao giờ** trả API key hay secrets trong bất kỳ response nào.

---

## 16. Best Practices

### Thiết kế tool tốt

```
✅ Tên tool rõ ràng: get_order, search_product, calculate_shipping
❌ Tên tool mơ hồ: do_stuff, process, handle

✅ Description cụ thể: "Lấy thông tin đơn hàng theo mã đơn hàng 8 ký tự"
❌ Description chung chung: "Lấy thông tin"

✅ Parameters có schema chặt chẽ với type, description, required
❌ Parameters rỗng {} hoặc quá lỏng lẻo
```

### Quản lý conversation

- Luôn lưu và gửi lại **đầy đủ** conversation history trong mỗi lượt.
- Không xóa hay sửa message `assistant` chứa `tool_calls`.
- `tool_call_id` trong `role="tool"` phải khớp **chính xác** với lượt trước.
- Đặt giới hạn số vòng lặp để tránh loop vô hạn trong ReAct Agent.

### Hiệu suất

- Dùng `stream=true` cho interactive UI để giảm thời gian chờ người dùng.
- Đặt `max_tokens` hợp lý để tránh response quá dài.
- Không truyền quá 32 tools trong một request — model sẽ khó chọn tool đúng.
- Dùng `tool_choice="required"` khi chắc chắn cần tool, tránh model trả lời tự do.
- Dùng `tool_choice="none"` khi chỉ cần chat, tránh validate tools không cần thiết.

### Xử lý kết quả

```python
# ✅ Luôn kiểm tra finish_reason trước khi xử lý
if choice.finish_reason == "tool_calls":
    # Xử lý tool calling
elif choice.finish_reason == "stop":
    # Xử lý final answer
elif choice.finish_reason == "length":
    # Model bị cắt do max_tokens — cần tăng max_tokens hoặc tóm tắt conversation
```

---

## 17. vLLM Backend Notes

### Kiến trúc

```
Client
  → OriAgent Public API (FastAPI, port 8089)
  → vLLM OpenAI-compatible server (port 8000)
```

- OriAgent Public API là lớp proxy xử lý auth, rate limit, validation.
- vLLM là inference backend thực sự.
- Không dùng Ollama.

### Khởi chạy vLLM với tool calling

Để hỗ trợ tool calling và auto tool choice, vLLM cần được chạy với parser phù hợp:

```bash
# Ví dụ với Qwen model
vllm serve Qwen/Qwen3.5-2B \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder

# Ví dụ với Hermes-format model
vllm serve model-name \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

### Lưu ý về tool calling

- Tool calling phụ thuộc vào khả năng của **model** và **parser** được chọn.
- Model nhỏ (< 3B params) có thể sinh tool arguments không ổn định — luôn validate trước khi execute.
- Với Qwen model, dùng parser `qwen3_coder` hoặc `hermes` tùy phiên bản.
- `--enable-auto-tool-choice` là bắt buộc để vLLM tự decode `tool_calls` từ output.

---

## 18. Checklist nhanh

Dùng checklist này để đảm bảo integration của bạn đúng:

### Tích hợp cơ bản
- [ ] Có Base URL đúng: `https://llm.oriagent.com/api/public/v1`
- [ ] Gửi `Authorization: Bearer YOUR_API_KEY` ở mọi request
- [ ] Gọi API từ backend, không từ frontend
- [ ] Xử lý HTTP error (4xx, 5xx)

### Chat Completion
- [ ] Request body có `model` và `messages`
- [ ] `messages` có ít nhất 1 phần tử
- [ ] Kiểm tra `finish_reason` trong response
- [ ] Đọc nội dung từ `choices[0].message.content`

### Tool Calling
- [ ] Tool schema đúng format OpenAI function schema
- [ ] `name` chỉ dùng ký tự `[a-zA-Z0-9_-]`
- [ ] Validate `function.arguments` (JSON string) trước khi execute
- [ ] Gửi Observation với `role="tool"` và đúng `tool_call_id`
- [ ] Echo nguyên vẹn message `assistant` chứa `tool_calls` trong lượt tiếp theo
- [ ] Đặt giới hạn số vòng lặp

### Observation
- [ ] `role="tool"` có trường `tool_call_id`
- [ ] `tool_call_id` khớp với `id` trong `tool_calls` lượt trước
- [ ] `content` của `role="tool"` là JSON string

### Internal ReAct Agent
- [ ] Gọi đúng endpoint `/agents/run` (không phải `/chat/completions`)
- [ ] Truyền `allowed_tools` — chỉ những tool đã đăng ký
- [ ] Đặt `max_steps` hợp lý (1–8)
- [ ] Đọc kết quả từ `answer`, không từ `choices`

### Security
- [ ] Không expose API key trong frontend
- [ ] Không hardcode API key trong source code
- [ ] Validate tool arguments trước khi execute
- [ ] Không gửi secrets trong `messages` hoặc tool `description`
