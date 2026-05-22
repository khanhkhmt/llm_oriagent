# Hướng Dẫn Chạy Dự Án Local

## Yêu cầu hệ thống

| Công cụ | Phiên bản tối thiểu | Kiểm tra |
|---------|---------------------|----------|
| Node.js | v18+ | `node --version` |
| Python | 3.10+ | `python3 --version` |
| npm | v9+ | `npm --version` |

---

## Cấu trúc thư mục

```
llm_oriagent/
├── backend/              ← FastAPI backend (Python)
│   ├── .venv/            ← Python virtual environment
│   ├── open_webui/       ← Source code backend
│   ├── data/             ← SQLite database (webui.db)
│   └── requirements.txt
├── src/                  ← SvelteKit frontend
├── start_backend.sh      ← Script khởi động backend
├── package.json
└── vite.config.ts
```

---

## Lần đầu cài đặt

### 1. Cài dependencies frontend

```bash
cd /home/khanhnq/llm_oriagent
npm install
```

### 2. Tạo Python virtual environment

```bash
cd /home/khanhnq/llm_oriagent/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> ⚠️ Nếu báo lỗi `peewee` không tương thích, cài đúng phiên bản:
> ```bash
> pip install peewee==3.19.0 peewee-migrate==1.14.3
> ```

---

## Chạy dự án (mỗi lần)

### Terminal 1 — Khởi động Backend

```bash
cd /home/khanhnq/llm_oriagent/backend
source .venv/bin/activate

GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com" \
GOOGLE_CLIENT_SECRET="your-google-client-secret" \
ENABLE_OAUTH_SIGNUP=True \
OAUTH_MERGE_ACCOUNTS_BY_EMAIL=True \
DEFAULT_USER_ROLE=user \
WEBUI_URL=http://localhost:5173 \
ENABLE_SIGNUP=True \
python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --workers 1
```

Hoặc dùng script có sẵn:

```bash
cd /home/khanhnq/llm_oriagent
bash start_backend.sh
```

> Backend sẵn sàng khi thấy: `Uvicorn running on http://0.0.0.0:8080`

### Terminal 2 — Khởi động Frontend Dev Server

```bash
cd /home/khanhnq/llm_oriagent
npm run dev
```

> Frontend sẵn sàng khi thấy: `Local: http://localhost:5173/`

---

## Truy cập ứng dụng

| Địa chỉ | Mô tả |
|---------|-------|
| `http://localhost:5173` | **Frontend** — Dùng địa chỉ này |
| `http://localhost:5173/signup` | Trang đăng ký |
| `http://localhost:5173/auth` | Trang đăng nhập |
| `http://localhost:8080/api/docs` | API documentation (Swagger) |

> ✅ Luôn dùng **`localhost:5173`** — có đầy đủ landing page, signup, hot-reload.
> `localhost:8080` là backend API, chỉ serve giao diện build cũ.

---

## Kiểm tra hoạt động

```bash
# Backend health check
curl http://localhost:8080/health
# → {"status":true}

# Kiểm tra Google OAuth
curl -I http://localhost:8080/oauth/google/login
# → HTTP/1.1 302 Found  (chứng tỏ OAuth hoạt động)

# Kiểm tra config
curl http://localhost:8080/api/config | python3 -m json.tool | grep -E "enable_signup|google"
```

---

## Tính năng đã cấu hình

| Tính năng | Trạng thái |
|-----------|-----------|
| Đăng ký bằng email | ✅ Bật |
| Đăng nhập Google OAuth | ✅ Bật |
| User mới tự động được duyệt | ✅ Bật (`DEFAULT_USER_ROLE=user`) |
| Merge tài khoản Google + Email | ✅ Bật |
| Landing page tại `/` | ✅ Có |
| Trang đăng ký tại `/signup` | ✅ Có |
| Sau đăng xuất về trang chủ | ✅ Về `/` |

---

## Biến môi trường quan trọng

| Biến | Giá trị | Mô tả |
|------|---------|-------|
| `GOOGLE_CLIENT_ID` | `your-client-id.apps.googleusercontent.com` | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | `your-client-secret` | Google OAuth Client Secret |
| `ENABLE_OAUTH_SIGNUP` | `True` | Cho phép tạo tài khoản qua Google |
| `OAUTH_MERGE_ACCOUNTS_BY_EMAIL` | `True` | Cho phép đăng nhập Google vào tài khoản email/pass cũ |
| `DEFAULT_USER_ROLE` | `user` | User mới không cần admin duyệt |
| `WEBUI_URL` | `http://localhost:5173` | URL frontend — sau OAuth redirect về đây |
| `ENABLE_SIGNUP` | `True` | Cho phép đăng ký bằng email/mật khẩu |

---

## Google Cloud Console — Cấu hình Redirect URI

Vào [console.cloud.google.com](https://console.cloud.google.com) → **APIs & Services → Credentials → OAuth 2.0 Client ID** → thêm:

```
Authorized redirect URIs:
  http://localhost:8080/oauth/google/callback
```

> Khi deploy lên domain thật, thêm thêm:
> `https://your-domain.com/oauth/google/callback`

---

## Build cho Production (deploy thật)

Khi muốn dùng chỉ 1 cổng `8080` (không cần `5173`):

```bash
# Bước 1: Build frontend
cd /home/khanhnq/llm_oriagent
NODE_OPTIONS="--max-old-space-size=4096" npm run build

# Bước 2: Chỉ cần chạy backend
bash start_backend.sh
# Truy cập tại: http://localhost:8080
```

> Build mất ~3-5 phút. Sau khi build, `localhost:8080` sẽ có đầy đủ UI mới.

---

## Xử lý lỗi thường gặp

### Lỗi: `inotify watch limit`
```bash
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Lỗi: `JavaScript heap out of memory` khi build
```bash
NODE_OPTIONS="--max-old-space-size=4096" npm run build
```

### Lỗi: `ModuleNotFoundError: No module named 'open_webui'`
Phải chạy uvicorn từ bên trong thư mục `backend/`:
```bash
cd /home/khanhnq/llm_oriagent/backend
.venv/bin/python -m uvicorn open_webui.main:app ...
```

### Backend không nhận config mới
Config được load lúc khởi động. Sau khi thay đổi biến môi trường hoặc DB, cần **restart backend**.

---

## Tài khoản

| Email | Role | Ghi chú |
|-------|------|---------|
| `nguyenquockhanh0909200513579@gmail.com` | Admin | Tài khoản quản trị |
| `khanh2005aiai@gmail.com` | User | Tài khoản thường |
