# agent_py

`agent_py` 是一个基于 FastAPI 的 AI 助手与多模型图像生成后端，集成了聊天接口、统一助手接口、批量生图、文件上传、会话历史、异步任务处理，以及本地/MinIO 存储能力。

项目的核心目标不是单一的“文生图 API”，而是提供一个可扩展的后端服务层，用统一的请求模型去调度多家模型供应商和多种工作流。

## 功能概览

- 多模型/多 Provider 适配，代码中已包含 `OpenAI`、`Gemini`、`Midjourney`、`Ideogram`、`Replicate`、`Fal.ai`、`百度`、`阿里云`、`腾讯` 等 provider 实现。
- `POST /api/v1/chat/completions` 提供 OpenAI 风格聊天接口，支持流式输出、会话上下文、图片/文档附件注入。
- `POST /api/v1/assistant/chat` 提供统一助手接口，可在聊天、单图生成、批量生成之间做路由。
- `POST /api/v1/generate`、`POST /api/v1/batch`、`POST /api/v1/generate-unified` 提供单图、批量和统一生图入口。
- `POST /v1/images/generations` 提供图像生成兼容接口，但当前返回的是异步任务信息，不是 OpenAI 官方 `data[].url` 结构。
- 文件管理接口支持上传、批量上传、下载、会话文件查询、MinIO 预签名 URL 等能力。
- 会话历史接口支持创建会话、保存消息、查询历史、生成摘要。
- 模型注册表支持从远端配置接口动态拉取模型与 provider 映射。
- 支持 PDF 提示词工作流，使用 LangChain/LangGraph 将 PDF 内容转为图像生成提示词。
- 使用 PostgreSQL 数据库，启动时自动建表。

## 适用场景

- 给前端应用提供统一的 AI 后端网关。
- 将聊天、附件理解、文生图、批量任务放到同一套 API 中管理。
- 对接中转站或多家供应商，减少前端直接适配不同接口的复杂度。
- 做带历史会话、文件上下文和异步任务轮询的图像生成产品。

## 项目结构

```text
agent_py/
├─ src/
│  ├─ api/                 FastAPI 入口、路由、中间件
│  ├─ config/              配置与模型注册表
│  ├─ database/            SQLAlchemy 模型与数据库管理
│  ├─ engine/              任务队列、Worker、批量任务调度
│  ├─ extractor/           基于 LLM 的参数提取
│  ├─ matcher/             参数增强与模板匹配
│  ├─ models/              Pydantic 请求/响应模型
│  ├─ parsers/             Excel/CSV/JSON/TXT/PDF/Word/Image 解析
│  ├─ providers/           各家模型供应商适配层
│  ├─ storage/             本地/MinIO 存储实现
│  ├─ utils/               上下文、加密、向量检索等工具
│  └─ workflows/           PDF 与附件相关 LangGraph 工作流
├─ data/                   本地数据存储目录（可选）
├─ doc/                    补充文档与 OpenAPI 导出
├─ examples/               调用示例
├─ logs/                   日志目录
├─ Dockerfile
├─ pyproject.toml
├─ requirements.txt
└─ uv.lock
```

## 运行要求

- Python `>=3.9`
- 推荐使用 `uv`
- 如需使用 `STORAGE_TYPE=minio`，需自行准备可访问的 MinIO/S3 兼容对象存储
- 如需调用聊天或模型接口，需要可用的 API Key

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

如果你使用 `pip`，也可以：

```bash
pip install -e .
```

### 2. 创建 `.env`

仓库当前没有提供 `.env.example`，可以直接新建 `.env`。  
开发环境建议先使用本地存储，否则默认 `minio` 配置可能导致启动时尝试连接对象存储。

最小可用示例：

```env
HOST=0.0.0.0
PORT=8888
DEBUG=false
LOG_LEVEL=INFO

# 建议本地开发先用 local
STORAGE_TYPE=local
STORAGE_PATH=./storage
STORAGE_URL_PREFIX=/storage

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_db

# 二选一：
# 1. 在这里配置默认 Key
# 2. 每次请求用 Authorization: Bearer <key> 传入
RELAY_API_KEY=

# 可选 OpenAI 直连配置
OPENAI_API_KEY=
OPENAI_BASE_URL=

DEFAULT_IMAGE_PROVIDER=openai
DEFAULT_LLM_PROVIDER=relay
DEFAULT_EMBEDDING_PROVIDER=relay

# 异步任务需要跨请求保存用户 Key 时，建议配置
CREDENTIAL_ENCRYPTION_KEY=replace-with-your-secret
```

如果要使用 MinIO，可额外配置：

```env
STORAGE_TYPE=minio
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=images
MINIO_SECURE=false
PUBLIC_BASE_URL=http://127.0.0.1:8080
MINIO_URL_PREFIX=/storage
```

说明：

- 环境变量大小写不敏感，`BaseSettings` 会自动读取 `.env`
- 数据库表会在应用启动时自动创建
- 异步任务表存储在主数据库中

### 3. 启动服务

```bash
uv run agent-py
```

或直接按模块启动：

```bash
uv run -m src
```

启动后可访问：

- Swagger UI: `http://127.0.0.1:8888/docs`
- ReDoc: `http://127.0.0.1:8888/redoc`
- 根路径状态: `http://127.0.0.1:8888/`

### 4. Docker 启动

```bash
docker build -t agent-py .
docker run --rm -p 8888:8888 --env-file .env agent-py
```

## 启动时会发生什么

应用启动时会自动完成以下初始化：

- 读取 `.env`
- 初始化主数据库并自动建表
- 初始化异步任务数据库
- 启动异步任务处理器
- 初始化模型注册表并拉取模型配置
- 启动内存任务队列和 Worker
- 当 `STORAGE_TYPE=local` 时挂载静态文件路由

如果远端模型配置接口不可用，应用仍可能启动，但模型列表相关接口会受影响。

## 常用接口

### 服务与健康检查

- `GET /`：服务基本信息
- `GET /health`：基础健康检查
- `GET /api/v1/health`：综合健康检查
- `GET /api/v1/health/storage`：存储健康检查

### 聊天与助手

- `POST /api/v1/chat/completions`：OpenAI 风格聊天接口
- `POST /api/v1/assistant/chat`：统一助手聊天/任务路由接口
- `POST /api/v1/assistant/upload`：助手附件上传

### 图像生成

- `POST /api/v1/generate`：单图生成
- `POST /api/v1/batch`：批量生成，可传 prompts 或上传文件
- `POST /api/v1/generate-unified`：统一图像生成/编辑接口
- `POST /v1/images/generations`：图像生成兼容接口

### 任务查询

- `GET /api/v1/tasks/{task_id}`：查询单任务状态
- `GET /api/v1/tasks/{task_id}/result`：获取任务结果
- `GET /api/v1/batch/{batch_id}`：查询批量任务状态
- `GET /api/async/status/{task_id}`：查询异步 provider 任务状态
- `GET /api/async/tasks`：列出异步任务

### 模型、文件、历史

- `GET /api/v1/models`：列出模型
- `GET /api/v1/models/{model_name}`：查看模型详情
- `POST /api/v1/models/refresh`：刷新模型缓存
- `POST /api/v1/files/upload`：上传文件
- `POST /api/v1/files/upload/batch`：批量上传文件
- `GET /api/v1/history/list`：列出会话
- `GET /api/v1/history/{session_id}`：查看会话详情

更完整的接口说明见 `doc/API_DOCUMENTATION.md`。

## 调用示例

### 单图生成

```bash
curl -X POST "http://127.0.0.1:8888/api/v1/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -d '{
    "prompt": "一只坐在窗边的橘猫，午后阳光，写实摄影风格",
    "model_name": "dall-e-3",
    "width": 1024,
    "height": 1024,
    "n": 1
  }'
```

### 聊天补全

```bash
curl -X POST "http://127.0.0.1:8888/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "帮我写一个适合电商海报的生图提示词"}
    ],
    "session_id": "demo-session",
    "enable_context": true,
    "stream": false
  }'
```

### 统一助手

```bash
curl -X POST "http://127.0.0.1:8888/api/v1/assistant/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -d '{
    "messages": [
      {"role": "user", "content": "参考我上传的文档，给我生成 3 张首页横幅图"}
    ],
    "session_id": "assistant-demo",
    "stream": false
  }'
```

## 关键实现说明

- `TaskManager` 负责内存任务队列、Worker 并发和批量任务调度。
- `DatabaseManager` 负责请求记录、生成记录、会话历史、文件记录、加密凭据存储。
- `ModelRegistry` 会从远端配置接口拉取模型清单，并建立模型到 provider 的映射。
- `workflows/pdf_prompt_graph.py` 负责将 PDF 内容转成结构化图像提示词。
- `storage/` 同时支持本地文件系统和 MinIO，两者通过统一结果模型返回 URL。

## 文档与示例

- `doc/API_DOCUMENTATION.md`：接口说明
- `doc/CONTEXT_MANAGEMENT.md`：上下文管理说明
- `examples/chat_with_context.py`：聊天上下文示例

## 开发说明

- 推荐使用 `uv.lock` 维护依赖；`requirements.txt` 更像导出结果。
- 当前主入口为 `src/api/main.py`，命令行入口为 `agent-py`。
- 如果你只是在本地调试，优先使用 `STORAGE_TYPE=local`。
- Relay 基础地址固定为 `https://api.yiwuxueshe.cn`，模型注册表固定使用 `https://api.yiwuxueshe.cn/api/pricing_new`。

## 已知差异与注意事项

- 聊天兼容接口路径是 `/api/v1/chat/completions`，不是 OpenAI 官方的 `/v1/chat/completions`。
- 图像兼容接口 `/v1/images/generations` 当前返回异步任务信息，而不是官方原始响应结构。
- 旧文档中提到的 `.env.example`、独立数据库初始化脚本、默认 `8000` 端口等信息与当前代码不一致，应以本 README 和源码为准。

## License

项目仓库当前未明确附带许可证文件；如需对外发布，请先补充 `LICENSE`。
