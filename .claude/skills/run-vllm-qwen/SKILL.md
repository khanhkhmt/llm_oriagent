---
name: run-vllm-qwen
description: Khởi động lại model Qwen/Qwen3.5-2B trên vLLM (port 8000) cho llm_oriagent — dùng khi public API / WebUI báo model server không chạy, hoặc khi được yêu cầu "chạy model".
---

# Chạy model Qwen/Qwen3.5-2B trên vLLM

Model này **mặc định tắt** để tiết kiệm GPU/RAM/đĩa (đã chủ động stop + xoá cache
ngày 2026-07-09 theo yêu cầu). Chỉ khởi động khi được yêu cầu.

## Kiến trúc liên quan

```
Client → https://llm.oriagent.com
  → Open WebUI backend  (pm2: llm-oriagent,      port 8089)
  → qwen-api proxy      (pm2: qwen-api,          port 8001)  ← WebUI chat nội bộ đi qua đây
  → vLLM                (pm2: vllm-qwen,         port 8000)  ← model chạy ở đây
Public API (/api/public/v1/*) trên 8089 gọi THẲNG vLLM 8000 (bỏ qua proxy).
Gateway phụ (pm2: vllm-api-gateway, port 8002) cũng gọi thẳng vLLM 8000.
```

GPU: RTX A5000 24GB, dùng chung với vLLM Qwen3-ASR (port 8004, ~9GB) và
voxcpm-backend (~4.4GB). Model này chiếm ~8GB (`--gpu-memory-utilization 0.35`).
**Trước khi chạy**: `nvidia-smi` — cần còn trống ≥ 9GB.

## Cách chạy (đường chuẩn — pm2 đã lưu sẵn app definition)

```bash
pm2 start vllm-qwen
```

Model weights (~4.3GB) sẽ tự tải lại từ HuggingFace nếu cache đã bị xoá
(`~/.cache/huggingface/hub/models--Qwen--Qwen3.5-2B`). Lần đầu mất ~4-5 phút;
nếu cache còn thì ~1 phút. Cần đĩa trống ≥ 6GB (`df -h /`).

Chờ sẵn sàng:

```bash
# Lặp tới khi trả về danh sách chứa Qwen3.5-2B (timeout hợp lý: 10 phút)
curl -s http://127.0.0.1:8000/v1/models | grep Qwen3.5-2B
```

Sau khi chạy, lưu trạng thái để sống sót qua reboot: `pm2 save`

## Nếu pm2 app `vllm-qwen` bị xoá mất — tạo lại từ đầu

```bash
cd /home/step/vLLM_oriagent && pm2 start venv/bin/python3 --name vllm-qwen \
  --max-memory-restart 10G -- \
  -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3.5-2B \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.35 \
  --tensor-parallel-size 1 \
  --enforce-eager \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --port 8000
```

Hai flag cuối **bắt buộc** cho public API tool-calling (branch
`feat/public-api-tool-calling-hardening` phụ thuộc parser `qwen3_coder`).

## Verify end-to-end sau khi lên

```bash
# 1. vLLM trực tiếp
curl -s http://127.0.0.1:8000/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"Qwen/Qwen3.5-2B","messages":[{"role":"user","content":"2+2=?"}],"max_tokens":50}'

# 2. Public API (key user lấy từ bảng api_key trong backend/data/webui.db)
curl -s https://llm.oriagent.com/api/public/v1/chat/completions \
  -H "Authorization: Bearer <api_key>" -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3.5-2B","messages":[{"role":"user","content":"Bạn là ai?"}],"max_tokens":100}'
# Kỳ vọng: tự xưng "Oriagent-2.1 Mini / Flash Lite ... AHT Tech" (không nói Qwen)
```

Model nhận cả 2 tên: `Qwen/Qwen3.5-2B` (nội bộ) và `Oriagent-2.1 Mini / Flash Lite`
(công khai) — mapping ở `backend/open_webui/routers/public/model_alias.py`.

## Tắt model (giải phóng GPU/RAM/đĩa)

```bash
pm2 stop vllm-qwen && pm2 save
rm -rf ~/.cache/huggingface/hub/models--Qwen--Qwen3.5-2B   # tuỳ chọn, lấy lại 4.3GB đĩa
```

Lưu ý khi model tắt: public API `/chat/completions`, `/agents/run` sẽ trả
502/503; WebUI chat với model này cũng lỗi. Health check 8089 vẫn OK.

## Log & chẩn đoán

- vLLM: `~/.pm2/logs/vllm-qwen-out.log`, `~/.pm2/logs/vllm-qwen-error.log`
- Backend: `~/.pm2/logs/llm-oriagent-out.log`
- Lỗi "System message must be at the beginning" từ vLLM = có 2 system message
  trong payload (chat template Qwen chỉ nhận 1, ở đầu).
