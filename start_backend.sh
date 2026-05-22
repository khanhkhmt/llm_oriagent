#!/bin/bash
cd /home/khanhnq/llm_oriagent/backend
source .venv/bin/activate

# Điền Google OAuth credentials của bạn vào đây
# Lấy tại: https://console.cloud.google.com → APIs & Services → Credentials
export GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-google-client-secret"

export ENABLE_OAUTH_SIGNUP=True
export OAUTH_MERGE_ACCOUNTS_BY_EMAIL=True
export DEFAULT_USER_ROLE=user
export WEBUI_URL=http://localhost:5173
export ENABLE_SIGNUP=True

exec python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --workers 1
