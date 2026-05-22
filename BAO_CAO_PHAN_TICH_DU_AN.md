# BÁO CÁO PHÂN TÍCH DỰ ÁN: Open WebUI

> **Ngày phân tích:** 2026-05-21  
> **Phiên bản dự án:** 0.9.5  
> **Người phân tích:** Claude Code (claude-sonnet-4-6)

---

## I. TỔNG QUAN DỰ ÁN

| Thuộc tính | Giá trị |
|------------|---------|
| **Tên dự án** | Open WebUI |
| **Phiên bản** | 0.9.5 |
| **Loại** | Self-hosted AI Platform (mã nguồn mở) |
| **Giấy phép** | Open WebUI License (bảo toàn branding bắt buộc) |
| **Repository** | https://github.com/open-webui/open-webui |

**Mô tả tổng quát:**  
Open WebUI là nền tảng giao diện web AI tự hosted, hỗ trợ hoạt động hoàn toàn offline. Hỗ trợ nhiều LLM runner (Ollama, OpenAI-compatible APIs, Anthropic, Google Gemini), tích hợp RAG (Retrieval-Augmented Generation), quản lý người dùng, công cụ mở rộng, voice, image generation, calendar, automations và nhiều tính năng enterprise.

---

## II. CẤU TRÚC THƯ MỤC

```
/home/khanhnq/llm_oriagent/
├── backend/                          # Backend Python/FastAPI
│   ├── open_webui/
│   │   ├── main.py                   # Điểm khởi động FastAPI chính
│   │   ├── config.py                 # Cấu hình runtime, migrations
│   │   ├── constants.py              # Hằng số (ERROR_MESSAGES, MESSAGES)
│   │   ├── env.py                    # Biến môi trường, logging, cấu hình device
│   │   ├── functions.py              # Hàm tiện ích chung
│   │   ├── tasks.py                  # Quản lý background tasks
│   │   ├── models/                   # SQLAlchemy data models (25+ model)
│   │   │   ├── chats.py              # Chat messages, lịch sử chat
│   │   │   ├── users.py              # Quản lý người dùng
│   │   │   ├── channels.py           # Group/DM channels
│   │   │   ├── knowledge.py          # RAG knowledge bases
│   │   │   ├── files.py              # Quản lý file upload
│   │   │   ├── prompts.py            # Prompt templates
│   │   │   ├── tools.py              # Custom tools
│   │   │   ├── skills.py             # Skills/extensions
│   │   │   ├── automations.py        # Scheduled tasks
│   │   │   ├── calendar.py           # Calendar events
│   │   │   ├── memories.py           # User memories
│   │   │   ├── notes.py              # Notes management
│   │   │   └── [13+ other models]
│   │   ├── routers/                  # FastAPI route handlers (28+ routers)
│   │   │   ├── chats.py              # Chat API (1.586 dòng)
│   │   │   ├── openai.py             # OpenAI API compatibility (1.624 dòng)
│   │   │   ├── ollama.py             # Ollama integration (1.695 dòng)
│   │   │   ├── retrieval.py          # RAG/retrieval (2.706 dòng - lớn nhất)
│   │   │   ├── channels.py           # Channel management (1.844 dòng)
│   │   │   ├── audio.py              # TTS/STT (1.559 dòng)
│   │   │   ├── images.py             # Image generation (1.085 dòng)
│   │   │   ├── knowledge.py          # Knowledge base (1.121 dòng)
│   │   │   ├── tools.py              # Tool management (930 dòng)
│   │   │   ├── prompts.py            # Prompt management (751 dòng)
│   │   │   ├── models.py             # Model management (739 dòng)
│   │   │   ├── auths.py              # Authentication (1.393 dòng)
│   │   │   ├── files.py              # File upload/management (827 dòng)
│   │   │   ├── scim.py               # SCIM 2.0 provisioning (1.016 dòng)
│   │   │   └── [15+ other routers]
│   │   ├── utils/                    # Utility modules (20+ files)
│   │   │   ├── auth.py               # JWT/token validation
│   │   │   ├── chat.py               # Chat utilities
│   │   │   ├── embeddings.py         # RAG embeddings
│   │   │   ├── code_interpreter.py   # Code execution
│   │   │   ├── models.py             # Model utilities
│   │   │   ├── plugin.py             # Plugin system
│   │   │   ├── sanitize.py           # HTML/content sanitization
│   │   │   ├── validate.py           # URL/input validation
│   │   │   ├── audit.py              # Audit logging
│   │   │   ├── asgi_middleware.py    # ASGI middleware
│   │   │   └── [10+ other utils]
│   │   ├── socket/
│   │   │   └── main.py               # Socket.IO server (real-time)
│   │   ├── internal/
│   │   │   ├── db.py                 # Database config (SQLAlchemy)
│   │   │   └── wrappers.py
│   │   └── storage/                  # Storage backends
│   ├── requirements.txt              # Python dependencies
│   ├── start.sh                      # Startup script production
│   └── dev.sh                        # Dev server script
│
├── src/                              # Frontend SvelteKit/TypeScript
│   ├── routes/
│   │   ├── (app)/                    # Main app routes (protected)
│   │   │   ├── home/                 # Chat home page
│   │   │   ├── workspace/            # Tools, skills, prompts, models, knowledge
│   │   │   ├── playground/           # Completions, images, chat testing
│   │   │   ├── notes/                # Notes management
│   │   │   ├── automations/          # Scheduled tasks
│   │   │   ├── calendar/             # Calendar view
│   │   │   ├── channels/             # Group/DM channels
│   │   │   ├── admin/                # Admin panel
│   │   │   │   ├── settings/
│   │   │   │   ├── users/
│   │   │   │   ├── functions/
│   │   │   │   ├── analytics/
│   │   │   │   └── evaluations/
│   │   │   └── c/[id]/               # Chat detail view
│   │   ├── auth/                     # Trang đăng nhập/đăng ký
│   │   ├── +layout.svelte            # Root layout
│   │   └── +error.svelte
│   ├── lib/
│   │   ├── components/               # Svelte UI components
│   │   │   ├── chat/                 # Chat components
│   │   │   ├── admin/                # Admin components
│   │   │   ├── workspace/            # Workspace components
│   │   │   ├── layout/               # Layout components
│   │   │   └── common/               # Shared components
│   │   ├── apis/                     # API client functions (31 subfolders)
│   │   ├── stores/                   # Svelte stores (state management)
│   │   ├── types/                    # TypeScript type definitions
│   │   ├── constants/                # Frontend constants
│   │   ├── i18n/                     # Internationalization
│   │   ├── utils/                    # Frontend utilities
│   │   └── workers/                  # Web workers (Pyodide, Kokoro)
│   ├── app.html
│   ├── app.css
│   └── tailwind.css
│
├── static/                           # Static assets (icons, images)
├── docs/                             # Documentation
├── cypress/                          # E2E testing
├── .github/                          # GitHub CI/CD workflows
│   └── workflows/
│       ├── docker-build.yaml
│       ├── format-build-frontend.yaml
│       ├── format-backend.yaml
│       └── release-pypi.yml
│
├── package.json                      # Node.js dependencies
├── pyproject.toml                    # Python build config
├── Dockerfile                        # Multi-stage Docker build
├── docker-compose.yaml               # Docker Compose standard
├── docker-compose.gpu.yaml           # Docker Compose với GPU
├── docker-compose.api.yaml           # Docker Compose API-only
├── docker-compose.otel.yaml          # Docker Compose + OpenTelemetry
├── tsconfig.json                     # TypeScript config
├── vite.config.ts                    # Vite bundler config
├── svelte.config.js                  # Svelte config
├── tailwind.config.js                # Tailwind CSS config
├── .env.example                      # Environment variables template
├── README.md
├── LICENSE
└── CHANGELOG.md
```

---

## III. PHÂN TÍCH TỪNG FILE QUAN TRỌNG

### 3.1 Backend Core

#### `backend/open_webui/main.py`
- **Mục đích:** Điểm khởi động chính của ứng dụng FastAPI
- **Chức năng chính:**
  - Khởi tạo FastAPI app với metadata (title, version, docs_url)
  - Mount tất cả 28+ routers
  - Đăng ký middleware: CORS, compression, session, auth, audit, WebSocket
  - Cấu hình static file serving (frontend build output)
  - Health check endpoint `/health`
- **Middleware stack (theo thứ tự):** Security headers → CORS → GZip → SessionMiddleware → Auth token → Audit logging → ASGI

#### `backend/open_webui/env.py`
- **Mục đích:** Load và validate toàn bộ biến môi trường (~600+ dòng)
- **Chức năng chính:**
  - Load từ `.env` file và OS environment
  - Khai báo hằng số cấu hình: DATABASE_URL, REDIS_URL, LLM API keys, v.v.
  - Cấu hình logging (Loguru, JSON format, level)
  - Phát hiện GPU device (CUDA/MPS/CPU) cho embeddings
  - Version/build hash tracking

#### `backend/open_webui/config.py`
- **Mục đích:** Runtime configuration - lưu và đọc settings từ database
- **Chức năng chính:**
  - `Config` table: lưu app settings dưới dạng JSON
  - Alembic auto-migrations khi khởi động
  - `PersistentConfig` class: reactive config với DB persistence
  - Feature flags runtime (bật/tắt tính năng không cần restart)

#### `backend/open_webui/constants.py`
- **Mục đích:** Định nghĩa hằng số toàn cục
- **Chứa:**
  - `ERROR_MESSAGES` - chuỗi lỗi chuẩn
  - `MESSAGES` - chuỗi thông báo
  - HTTP status codes
  - Default values

#### `backend/open_webui/internal/db.py`
- **Mục đích:** Cấu hình SQLAlchemy, connection pooling, migrations
- **Chức năng chính:**
  - Tạo async engine dựa theo `DATABASE_URL`
  - SQLite: WAL mode, pragma tuning (cache=64MB, mmap=268MB)
  - PostgreSQL/MySQL: connection pool, SSL
  - `get_async_session()` dependency cho FastAPI
  - Alembic migration runner

#### `backend/open_webui/socket/main.py`
- **Mục đích:** Quản lý WebSocket real-time qua Socket.IO
- **Chức năng chính:**
  - Socket.IO server với Redis adapter (multi-worker)
  - Session pool: mapping user_id ↔ socket sessions
  - Sự kiện: `connect`, `disconnect`, `message`, `usage`
  - Broadcast messages tới clients liên quan
  - Real-time typing indicators, message updates

### 3.2 Backend Models (SQLAlchemy)

#### `models/chats.py`
- **Tables:** `Chat`, `ChatMessage`
- **Quan hệ:** ChatMessage có `parent_id` → cây hội thoại (branching)
- **Fields quan trọng:** `id`, `user_id`, `title`, `meta`, `folder_id`, `pinned`, `share_id`, `archived`
- **Features:** Soft delete, shared link, folder organization, pinning

#### `models/users.py`
- **Tables:** `User`, `UserGroup`, `UserGroupMember`
- **Fields:** `role` (admin/user/pending), `permissions` (JSON), `profile_image_url`, `api_key`, `last_active_at`
- **RBAC:** role-based + granular permission JSON per user

#### `models/channels.py`
- **Tables:** `Channel`, `ChannelMember`, `ChannelMessage`
- **Types:** group channels, DM (direct message)
- **Features:** streaming support, tool calling, message ownership

#### `models/knowledge.py`
- **Tables:** `Knowledge`, `KnowledgeFile`
- **Quan hệ:** Một knowledge có nhiều files, mỗi file có vector embeddings
- **Access control:** public/private/group-based

#### `models/files.py`
- **Tables:** `File`
- **Fields:** `filename`, `meta` (MIME type, size), `user_id`, `hash` (dedup)
- **Storage:** local filesystem hoặc cloud (S3, GCS, Azure, GDrive, OneDrive)

### 3.3 Backend Routers

#### `routers/retrieval.py` (2.706 dòng - lớn nhất)
- **Mục đích:** Toàn bộ RAG pipeline
- **Endpoints chính:**
  - `POST /process/file` - ingest file vào vector DB
  - `POST /process/web` - ingest URL/web content
  - `POST /query/collection` - vector similarity search
  - `POST /query/doc` - search trong document cụ thể
  - `GET /ef` - embedding function info
- **Pipeline:** File → Extract text → Chunk → Embed → Store vector DB → Retrieve → Inject context

#### `routers/chats.py` (1.586 dòng)
- **Mục đích:** CRUD chat history, branching, export
- **Endpoints chính:**
  - `GET /` - list chats (pagination, search, filter)
  - `POST /new` - tạo chat mới
  - `GET /{id}` - lấy chi tiết chat
  - `POST /{id}/messages` - thêm message
  - `PUT /{id}/messages/{message_id}` - edit message
  - `POST /{id}/share` - tạo public share link
  - `GET /export` - export all chats (JSON)
  - `POST /import` - import chats

#### `routers/openai.py` (1.624 dòng)
- **Mục đích:** OpenAI-compatible API proxy layer
- **Endpoints:**
  - `POST /chat/completions` - streaming/non-streaming completions
  - `GET /models` - list available models
  - `POST /embeddings` - text embeddings
  - `POST /audio/transcriptions` - STT proxy
- **Logic:** Auth → model resolution → request forwarding → response streaming → usage tracking

#### `routers/ollama.py` (1.695 dòng)
- **Mục đích:** Native Ollama integration
- **Endpoints:**
  - `GET /api/tags` - list Ollama models
  - `POST /api/generate` - text generation
  - `POST /api/chat` - chat completion
  - `POST /api/pull` - pull model từ registry
  - `POST /api/push` - push custom model
  - `POST /api/create` - tạo Modelfile
  - `DELETE /api/delete` - xóa model

#### `routers/auths.py` (1.393 dòng)
- **Mục đích:** Authentication, authorization, user management
- **Endpoints:**
  - `POST /signin` - đăng nhập (JWT token)
  - `POST /signup` - đăng ký tài khoản
  - `GET /me` - current user info
  - `POST /password/update` - đổi mật khẩu
  - `GET /oauth/{provider}` - OAuth redirect
  - `GET /oauth/{provider}/callback` - OAuth callback
  - `POST /logout` - đăng xuất, back-channel logout
  - API key management

#### `routers/audio.py` (1.559 dòng)
- **Mục đích:** Speech-to-Text và Text-to-Speech
- **STT providers:** Local Whisper (faster-whisper), OpenAI Whisper API, Deepgram, Azure Speech
- **TTS providers:** Azure, ElevenLabs, OpenAI TTS, Transformers (local), Browser WebSpeech API
- **Endpoints:**
  - `POST /transcriptions` - âm thanh → text
  - `POST /speech` - text → âm thanh

#### `routers/channels.py` (1.844 dòng)
- **Mục đích:** Group channels và Direct Messages
- **Endpoints:**
  - `GET /` - list channels
  - `POST /create` - tạo channel
  - `POST /{id}/messages` - gửi message (streaming)
  - `PUT /{id}/messages/{message_id}` - edit (kiểm tra ownership)
  - `DELETE /{id}/messages/{message_id}` - xóa (ownership/admin)
  - `POST /{id}/messages/{message_id}/pin` - pin message

#### `routers/images.py` (1.085 dòng)
- **Providers:** DALL-E (OpenAI), Gemini Imagen, ComfyUI (local), AUTOMATIC1111 (local SD)
- **Endpoints:**
  - `POST /generations` - tạo ảnh từ prompt
  - `GET /models` - list image models
  - `POST /edit` - chỉnh sửa ảnh

#### `routers/scim.py` (1.016 dòng)
- **Mục đích:** SCIM 2.0 automated user/group provisioning
- **Tích hợp:** Azure AD, Okta, các IdP hỗ trợ SCIM
- **Endpoints:**
  - `GET /Users` - list users
  - `POST /Users` - tạo user
  - `PATCH /Users/{id}` - update/deactivate
  - `GET /Groups` - list groups
  - `POST /Groups` - tạo group

### 3.4 Backend Utils

#### `utils/auth.py`
- JWT token encode/decode
- `get_verified_user()` FastAPI dependency
- API key validation
- Permission checking helpers

#### `utils/embeddings.py`
- Sentence-Transformers model loading (lazy)
- Embedding generation function
- Batch processing support
- Model caching

#### `utils/sanitize.py`
- HTML sanitization (XSS prevention)
- Markdown content filtering
- Allowlist-based tag/attribute filtering

#### `utils/validate.py`
- URL validation (SSRF protection)
- Redirect chain blocking
- MIME type checking
- Input length validation

#### `utils/audit.py`
- Structured audit log writing
- Resource change tracking (create/update/delete)
- User attribution
- OpenTelemetry integration

#### `utils/plugin.py`
- Custom function/tool loading
- Python sandbox execution (RestrictedPython)
- Dependency installation for functions
- MCP client integration

### 3.5 Frontend

#### `src/routes/+layout.svelte`
- Root layout: kiểm tra auth state, redirect nếu chưa đăng nhập
- Version polling (kiểm tra update từ server)
- Global error boundary
- Theme initialization (dark/light mode)
- i18n language loading

#### `src/routes/(app)/home/`
- Main chat interface
- Sidebar: danh sách chat, search, folders
- Model selector dropdown
- System prompt input
- New chat button

#### `src/routes/(app)/c/[id]/`
- Chi tiết một cuộc chat
- Message list với streaming
- Message editing, branching
- File attachment upload
- Tool call display
- RAG citation display

#### `src/routes/(app)/workspace/`
- **models/**: quản lý custom model definitions
- **tools/**: tạo/edit custom tools (Python editor)
- **prompts/**: prompt template library
- **knowledge/**: document collection management
- **functions/**: Python function editor với dependency management

#### `src/routes/(app)/admin/`
- **settings/**: system settings, model config, auth config
- **users/**: user list, roles, permissions
- **analytics/**: usage statistics, model usage charts
- **evaluations/**: feedback rating management

#### `src/lib/stores/`
- `user.ts` - current user state
- `settings.ts` - user preferences
- `models.ts` - available model list
- `chats.ts` - chat list state
- `theme.ts` - dark/light mode

#### `src/lib/apis/`
- Một file/folder per entity (chats, models, tools, knowledge, files, v.v.)
- Wrap fetch() với auth headers, error handling
- TypeScript typed responses

### 3.6 Configuration Files

#### `package.json`
```json
{
  "name": "open-webui",
  "version": "0.9.5",
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```
- **Dev dependencies:** SvelteKit, Vite, TypeScript, Tailwind CSS, Cypress
- **Runtime dependencies:** bits-ui, tipTap, mermaid, marked, socket.io-client, i18next, kokoro-js

#### `pyproject.toml`
- Build system: Hatchling
- Package: `open-webui` publish to PyPI
- Entry point: `open-webui serve`
- Python version: ≥ 3.11

#### `Dockerfile`
- **Stage 1 (Node):** `npm run build` → build frontend static files
- **Stage 2 (Python):** copy frontend build + install Python deps + copy backend
- Base image: `python:3.11-slim`
- Port: 8080
- Entrypoint: `bash start.sh`

#### `docker-compose.yaml`
- Services: `ollama` + `open-webui`
- Networks: isolated bridge network
- Volumes: persistent data (`open-webui`, `ollama`)
- GPU profiles: `cpu`, `gpu-nvidia`, `gpu-amd`

#### `.env.example`
- 100+ biến cấu hình với comments
- Nhóm: Server, Database, Auth, LLM backends, RAG, Storage, Security, Monitoring

---

## IV. CÔNG NGHỆ & FRAMEWORK

### 4.1 Backend Stack

| Lớp | Công nghệ | Phiên bản |
|-----|-----------|-----------|
| Framework | FastAPI | 0.135.1 |
| Server | Uvicorn | 0.41.0 |
| ORM | SQLAlchemy (async) | 2.0.48 |
| Validation | Pydantic | 2.12.5 |
| DB chính | SQLite (WAL) / PostgreSQL / MySQL / MongoDB | - |
| Cache | Redis (Sentinel support) | 7.4.0 |
| Auth | JWT (PyJWT), OAuth (authlib), bcrypt/argon2 | - |
| OpenAI SDK | openai | 2.29.0 |
| Anthropic SDK | anthropic | 0.86.0 |
| Google GenAI | google-genai | 1.66.0 |
| RAG | LangChain | 1.2.10 |
| MCP | mcp | 1.26.0 |
| Vector DB | ChromaDB, Weaviate, Qdrant, Milvus, Pinecone, Elasticsearch, PGVector | - |
| Embeddings | sentence-transformers | 5.4.0 |
| STT | faster-whisper | - |
| Scheduling | APScheduler | 3.11.2 |
| Monitoring | OpenTelemetry, Loguru | - |
| WebSocket | Socket.IO (python-socketio) | - |

### 4.2 Frontend Stack

| Lớp | Công nghệ | Phiên bản |
|-----|-----------|-----------|
| Framework | SvelteKit | 2.5.27 |
| Build tool | Vite | 5.4.21 |
| Styling | Tailwind CSS | 4.0.0 |
| UI Library | Bits UI | 2.0.0 |
| Rich Text | TipTap | 3.0.7 |
| Markdown | Marked | 9.1.0 |
| Diagrams | Mermaid | 11.10.1 |
| Browser AI | @huggingface/transformers | 3.0.0 |
| TTS (browser) | Kokoro-JS | 1.1.1 |
| Python (browser) | Pyodide | 0.28.2 |
| WebSocket | Socket.IO client | 4.2.0 |
| i18n | i18next | 23.10.0 |
| Security | DOMPurify | - |

---

## V. KIẾN TRÚC HỆ THỐNG

### 5.1 Request Flow (Backend)

```
Client Request
    │
    ▼
FastAPI App (main.py)
    │
    ├─ Security Headers Middleware
    ├─ CORS Middleware
    ├─ GZip Compression
    ├─ Session Middleware (Redis-backed)
    ├─ Auth Token Validation
    └─ Audit Logging Middleware
         │
         ▼
    Router (28+ routers)
         │
         ├─ get_verified_user() dependency → JWT validation
         ├─ has_permission() → RBAC check
         └─ get_async_session() dependency → DB session
              │
              ▼
         Business Logic
              │
              ├─ Model Layer (SQLAlchemy)
              ├─ LLM Client (OpenAI/Ollama/Anthropic)
              ├─ Vector DB (RAG)
              └─ Storage (local/cloud)
```

### 5.2 Chat Completion Flow

```
User sends message
    │
    ▼
POST /api/chat/completions
    │
    ├─ Auth validation
    ├─ Model resolution (user model → provider)
    ├─ Permission check (model access)
    ├─ Tool resolution (attached tools)
    ├─ RAG context injection (nếu có knowledge)
    ├─ Request forwarding → LLM provider
    │       ├─ OpenAI: openai.py router
    │       ├─ Ollama: ollama.py router
    │       └─ Others: custom clients
    ├─ Streaming response (Server-Sent Events)
    ├─ Tool call execution (nếu model gọi tools)
    ├─ Message save to DB
    └─ Usage tracking → Socket.IO broadcast
```

### 5.3 RAG Pipeline

```
Document Input (file/URL/web search)
    │
    ▼
Content Extraction
    ├─ PDF: PyPDF / Docling / Document Intelligence
    ├─ Web: BeautifulSoup / Playwright
    ├─ Office: python-pptx, pandoc
    ├─ OCR: PaddleOCR / Mistral OCR / Tika
    └─ Other: Unstructured
         │
         ▼
Text Chunking (configurable chunk size & overlap)
         │
         ▼
Embedding Generation (sentence-transformers)
         │
         ▼
Vector Storage
    ├─ ChromaDB (default, local)
    ├─ Weaviate, Qdrant, Milvus, Pinecone
    ├─ Elasticsearch, PGVector
    └─ OpenAI Embeddings
         │
         ▼
Retrieval (query time)
    ├─ Vector similarity search
    ├─ BM25 keyword search
    └─ Hybrid reranking
         │
         ▼
Context injection vào LLM prompt
```

### 5.4 Frontend Architecture

```
SvelteKit App
    │
    ├─ Stores (reactive state)
    │   ├─ user, settings, models, chats
    │   └─ theme, notifications
    │
    ├─ Routes (pages)
    │   ├─ (app)/ → protected routes
    │   │   ├─ home/ → chat list + new chat
    │   │   ├─ c/[id]/ → chat detail
    │   │   ├─ workspace/ → tools, models, knowledge
    │   │   ├─ admin/ → system management
    │   │   ├─ channels/ → group/DM
    │   │   └─ notes/, calendar/, automations/
    │   └─ auth/ → login/signup
    │
    ├─ Components
    │   ├─ chat/ → ChatInput, MessageList, ModelSelector
    │   ├─ common/ → Button, Modal, Tooltip, Toast
    │   └─ admin/ → UserTable, SettingsForm
    │
    ├─ APIs (fetch wrappers)
    │   └─ Per entity: chats, models, tools, knowledge, files...
    │
    └─ Workers (Web Workers)
        ├─ Pyodide worker → Python code execution in browser
        └─ Kokoro worker → TTS audio generation in browser
```

---

## VI. CÁC TÍNH NĂNG CHÍNH

### 6.1 Chat & Conversation
- Multi-model conversation (chọn nhiều model cùng lúc)
- Streaming responses (Server-Sent Events)
- Branching chat history (parent_id graph)
- Chat sharing via public link
- Import/Export chat history (JSON)
- Folders và pinning để tổ chức
- Tìm kiếm trong chat history
- Usage statistics per message

### 6.2 Model Management
- Hỗ trợ: Ollama, OpenAI-compatible, Anthropic, Google Gemini, Azure OpenAI
- Custom model builder (Modelfile-based)
- Model parameter customization (temperature, top_p, context length)
- Profile image cho model
- Access control per model (public/private/group)
- Model capability detection (vision, tools, v.v.)

### 6.3 RAG & Knowledge
- 9 vector database backends
- 5+ content extraction engines (Tika, Docling, Mistral OCR, PaddleOCR, Document Intelligence)
- Hybrid search: BM25 + vector similarity
- Web search integration (15+ providers: Google PSE, Brave, Kagi, Tavily, DuckDuckGo, v.v.)
- Knowledge collections với phân quyền
- Document-level citation trong responses
- Auto-chunking với configurable size/overlap

### 6.4 Voice & Audio
- **STT:** Local Whisper, OpenAI, Deepgram, Azure Speech
- **TTS:** Azure, ElevenLabs, OpenAI, Transformers (local), Browser API, Kokoro (browser)
- Voice mode với auto-transcription
- Mute/unmute control
- Audio file upload & processing

### 6.5 Image Generation
- **Providers:** DALL-E 3, Gemini Imagen, ComfyUI (local), AUTOMATIC1111 Stable Diffusion
- Prompt-based generation
- Image editing
- Size/quality parameters

### 6.6 Tools & Extensions
- Custom Python tool editor (in-browser)
- OpenAPI spec import (third-party tools)
- Tool server (external tool services)
- MCP (Model Context Protocol) client
- Native function calling
- Dependency installation cho tools

### 6.7 Channels (Group & DM)
- Group channels với access control
- Direct messages giữa users
- Streaming trong channels
- Tool calling trong channels
- Message pinning (write permission required)
- Message ownership enforcement
- Edit/delete với authorization

### 6.8 Notes
- Rich text editor (TipTap)
- Pin notes
- Per-user (không chia sẻ)
- Folder organization

### 6.9 Calendar & Automations
- Calendar events với ownership
- Scheduled automations (RRULE support)
- Automation limit per user
- Date-based task organization

### 6.10 Admin Features
- User management (roles, permissions, groups)
- Model management (enable/disable, access)
- System settings (JSON config)
- Analytics (usage charts, model breakdown)
- Feedback/evaluation management
- Audit logging
- Health check endpoints
- Function deployment

### 6.11 Enterprise Features
- LDAP/Active Directory integration
- SCIM 2.0 automated provisioning
- SSO via trusted headers
- OAuth token exchange
- Back-Channel Logout
- Cloud storage: Google Drive, OneDrive/SharePoint, S3, Azure Blob
- OpenTelemetry monitoring
- Multi-worker Redis-backed sessions
- Kubernetes deployment support

---

## VII. DATA MODELS QUAN TRỌNG

| Model | Table | Mục đích | Fields quan trọng |
|-------|-------|----------|-------------------|
| User | `user` | Quản lý tài khoản | id, name, email, role, permissions (JSON), api_key |
| Chat | `chat` | Cuộc hội thoại | id, user_id, title, folder_id, share_id, archived, pinned |
| ChatMessage | `chatmessage` | Tin nhắn | id, chat_id, parent_id, role, content, model, usage |
| Channel | `channel` | Group/DM | id, name, type, user_id, access (JSON) |
| ChannelMessage | `channelmessage` | Tin nhắn channel | id, channel_id, user_id, parent_id, content |
| File | `file` | File upload | id, user_id, filename, meta (MIME, size), hash |
| Knowledge | `knowledge` | Document library | id, user_id, name, description, access (JSON) |
| Model | `model` | LLM definition | id, name, base_model_id, params (JSON), access |
| Prompt | `prompt` | Template | id, command, title, content (với variables) |
| Tool | `tool` | Custom tool | id, name, content (Python), specs (JSON) |
| Skill | `skill` | Extension script | id, name, content, access |
| Function | `function` | Python snippet | id, name, content, is_active, is_global |
| Automation | `automation` | Scheduled task | id, user_id, name, actions (JSON), rrule |
| Calendar | `calendar` | Event | id, user_id, title, start, end, meta |
| Note | `note` | Rich text | id, user_id, title, content, pinned |
| Memory | `memory` | Persistent context | id, user_id, content |
| Feedback | `feedback` | Evaluation | id, user_id, data (JSON - ratings, comments) |
| Tag | `tag` | Labels | id, name, user_id |
| Folder | `folder` | Organization | id, name, user_id, parent_id |
| AccessGrant | `accessgrant` | Permissions | id, user_id, resource_type, resource_id |
| Config | `config` | App settings | id, data (JSON) |
| OAuthSession | `oauthsession` | OAuth state | id, user_id, provider, token |

---

## VIII. API ENDPOINTS TỔNG HỢP

| Router | Prefix | Số endpoints ước tính | Chức năng chính |
|--------|--------|----------------------|-----------------|
| retrieval | `/retrieval` | ~20 | RAG, embed, search |
| chats | `/chats` | ~25 | CRUD chat, messages, share |
| openai | `/openai` | ~10 | OpenAI proxy |
| ollama | `/ollama` | ~15 | Ollama proxy |
| channels | `/channels` | ~20 | Group/DM messaging |
| audio | `/audio` | ~8 | STT, TTS |
| images | `/images` | ~6 | Image generation |
| knowledge | `/knowledge` | ~15 | Document collections |
| tools | `/tools` | ~10 | Tool CRUD |
| auths | `/auths` | ~15 | Auth, OAuth |
| files | `/files` | ~10 | File management |
| scim | `/scim/v2` | ~12 | SCIM provisioning |
| models | `/models` | ~10 | Model management |
| prompts | `/prompts` | ~8 | Prompt templates |
| users | `/users` | ~15 | User management (admin) |
| memories | `/memories` | ~8 | Persistent memory |
| notes | `/notes` | ~8 | Notes CRUD |
| automations | `/automations` | ~8 | Scheduled tasks |
| calendar | `/calendar` | ~8 | Calendar events |
| skills | `/skills` | ~10 | Skills management |
| functions | `/functions` | ~10 | Function CRUD |
| [others] | various | ~50 | Health, config, analytics... |

---

## IX. BẢO MẬT

### 9.1 Authentication & Authorization
- JWT tokens với expiration
- API key support (custom header configurable)
- OAuth 2.0 (Google, GitHub, Azure AD, Okta, v.v.)
- LDAP/Active Directory
- Trusted header SSO
- SCIM 2.0 provisioning
- Role-Based Access Control (admin/user/pending)
- Granular permissions JSON per user/group

### 9.2 Vulnerability Mitigations

| Vulnerability | Biện pháp |
|--------------|-----------|
| XSS | DOMPurify, HTML sanitization (utils/sanitize.py), CSP headers |
| SSRF | URL validation (utils/validate.py), redirect blocking (`AIOHTTP_CLIENT_ALLOW_REDIRECTS=False`) |
| CSRF | SameSite cookies, SessionMiddleware tokens |
| SQL Injection | Parameterized queries qua SQLAlchemy ORM |
| Mass Assignment | Field-level filtering, Pydantic models |
| Clickjacking | X-Frame-Options, iframe CSP (`IFRAME_CSP`) |
| Path Traversal | Input validation, path normalization |
| Feedback Spoofing | User attribution enforcement (user_id từ JWT, không từ request body) |
| File Ownership | Verification trước khi process |
| Profile Image | MIME-type allowlist |

### 9.3 Data Protection
- HTTPS enforcement (configurable)
- Secure cookies (SameSite=Strict, HttpOnly)
- Password hashing: bcrypt + argon2
- SQLCipher encryption option
- Audit logging cho resource changes

---

## X. HIỆU SUẤT & TỐI ƯU HÓA

### 10.1 Database
- SQLite WAL mode (concurrent reads)
- Pragma tuning: `cache_size=-65536` (64MB), `mmap_size=268435456` (256MB), `synchronous=NORMAL`
- Connection pooling (PostgreSQL/MySQL)
- Async SQLAlchemy (non-blocking queries)
- Aiocache (query result caching)

### 10.2 Backend
- Async/await throughout (FastAPI, SQLAlchemy async)
- GZip compression middleware
- Background tasks (APScheduler)
- Lazy model loading (embeddings loaded on first use)
- Batch embedding processing

### 10.3 Frontend
- `content-visibility: auto` cho large chat lists
- Lazy loading routes & components
- Web Workers cho heavy tasks (Pyodide, Kokoro TTS)
- LocalStorage caching cho settings/preferences
- Svelte reactive stores (minimal re-renders)
- Vite code splitting

### 10.4 Scalability
- Redis adapter cho Socket.IO (multi-worker)
- Redis session sharing (stateless backend)
- Multiple database backend support
- Cloud storage backends (không giới hạn local disk)
- Kubernetes deployment với horizontal scaling

---

## XI. CI/CD & DEPLOYMENT

### 11.1 GitHub Actions Workflows
| Workflow | Trigger | Mục đích |
|----------|---------|----------|
| `docker-build.yaml` | push main/tags | Build & push Docker image |
| `format-build-frontend.yaml` | PR | Lint + build frontend |
| `format-backend.yaml` | PR | Black, isort formatting check |
| `release-pypi.yml` | tag push | Publish to PyPI |

### 11.2 Docker Images
- `ghcr.io/open-webui/open-webui:main` - Standard (CPU)
- `ghcr.io/open-webui/open-webui:cuda` - NVIDIA GPU
- `ghcr.io/open-webui/open-webui:ollama` - Bundled với Ollama
- `ghcr.io/open-webui/open-webui:dev` - Development build

### 11.3 Docker Compose Variants
```bash
# Standard với Ollama
docker compose up -d

# GPU support
docker compose -f docker-compose.gpu.yaml up -d

# API-only (no Ollama)
docker compose -f docker-compose.api.yaml up -d

# Với OpenTelemetry monitoring
docker compose -f docker-compose.otel.yaml up -d
```

### 11.4 Kubernetes
- Kustomize configurations provided
- Helm chart support
- Persistent volume claims cho data
- ConfigMap cho environment variables

---

## XII. TESTING

| Loại test | Tool | Coverage |
|-----------|------|----------|
| E2E | Cypress | Chat flows, auth, admin |
| E2E | Playwright | Cross-browser |
| Backend unit | pytest | Utilities, models |
| Integration | pytest-docker | DB, Redis integration |
| Performance | Locust (optional) | Load testing |

---

## XIII. INTERNATIONALIZATION

- 50+ ngôn ngữ được hỗ trợ
- i18next với namespace splitting
- Auto language detection từ browser
- Manual language switching trong settings
- RTL support (Arabic, Hebrew)
- Date/time localization (dayjs)

---

## XIV. THAY ĐỔI GẦN ĐÂY (v0.9.3 - v0.9.5)

### Bảo mật (Security Fixes)
- SSRF protection via redirect blocking
- Iframe CSP enforcement
- Profile image MIME-type allowlist
- Feedback attribution spoofing prevention
- File ownership verification in RAG
- Tool source code authorization
- Channel message ownership enforcement
- Model parameter exposure fix cho read-only users
- Skill public sharing permission enforcement

### Tính năng mới
- Granular markdown rendering controls
- Channel streaming & tool support
- Notes creation reliability improvements
- Legacy chat history self-healing
- Voice recording MIME format fallback
- Multi-device camera selection memory

---

## XV. ĐÁNH GIÁ KIẾN TRÚC

### Điểm Mạnh

| # | Điểm mạnh | Mô tả |
|---|-----------|-------|
| 1 | Full-stack monorepo | Frontend + Backend cùng repo, dễ phát triển |
| 2 | Async throughout | FastAPI + SQLAlchemy async → không blocking |
| 3 | Comprehensive RAG | 9 vector DB backends, nhiều extraction engines |
| 4 | Enterprise-ready | SCIM, LDAP, OAuth, RBAC, audit logging |
| 5 | Security-first | SSRF, XSS, CSRF protections built-in |
| 6 | Extensible | Plugin system, MCP, custom tools, OpenAPI import |
| 7 | Multi-provider | OpenAI, Ollama, Anthropic, Google, Azure |
| 8 | Self-hostable | Offline-capable, no external dependencies required |

### Điểm Yếu / Cần Cải Thiện

| # | Vấn đề | Tác động |
|---|--------|----------|
| 1 | Monolithic backend | 28+ routers, khó maintain khi scale |
| 2 | Tight coupling | Chat ↔ RAG ↔ Models ↔ Tools phụ thuộc chặt chẽ |
| 3 | Router size | retrieval.py 2.706 dòng, channels.py 1.844 dòng |
| 4 | Auto migrations | Alembic chạy tự động khi startup → risk ở production |
| 5 | Test coverage | Unit tests hạn chế, chủ yếu E2E |
| 6 | No service layer | Business logic trực tiếp trong routers |
| 7 | API versioning | Không có versioning strategy (v1, v2) |

### Khuyến Nghị

1. **Tách service layer:** Move business logic từ routers sang dedicated service classes
2. **Microservices (nếu cần scale):** Tách auth, RAG, LLM proxy thành services riêng
3. **API versioning:** Thêm `/api/v1/` prefix để hỗ trợ backwards compatibility
4. **Unit testing:** Thêm pytest unit tests cho models và utils
5. **Migration safety:** Tách migration step ra khỏi startup, chạy riêng trong CI
6. **Circuit breakers:** Thêm retry/timeout logic cho LLM provider calls
7. **Rate limiting:** Per-user request limiting cho API endpoints

---

## XVI. KẾT LUẬN

Open WebUI là một dự án **full-featured, production-ready** với kiến trúc phức tạp nhưng có cấu trúc tốt. Dự án phù hợp cho:

- **Self-hosted AI deployment** cho tổ chức muốn kiểm soát dữ liệu
- **Enterprise deployment** với LDAP, SCIM, SSO, multi-tenancy
- **Research & development** với RAG pipeline linh hoạt
- **Multi-model experimentation** với nhiều LLM provider

Codebase lớn (~30K+ dòng backend, ~50K+ dòng frontend) nhưng được tổ chức tốt với router pattern rõ ràng và separation of concerns hợp lý. Bảo mật được chú trọng với nhiều lớp protection.

---

*Báo cáo được tạo tự động bởi Claude Code (claude-sonnet-4-6) ngày 2026-05-21*
