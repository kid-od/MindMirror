# MindMirror 项目说明

Agent的项目记录，方便后续持续更新与展示。

## 本地部署

### 1) 环境准备
- Python `3.12+`
- 包管理建议：`uv`（也支持 `pip`）
- Docker / Docker Compose（用于启动 Milvus 依赖）

### 2) 使用 pyproject 安装依赖
在项目根目录执行：

```bash
# 方式 A：推荐（uv）
uv sync

# 运行服务
uv run python backend/app.py
# 或
uv run uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# 方式 B：pip
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .

# 运行服务
python backend/app.py
# 或
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

### 3) 创建 `.env` 文件
在项目根目录新建 `.env`，可直接使用下面模板：

```env
# ===== Model =====
ARK_API_KEY=your_dashscope_api_key
MODEL=qwen3.6-plus
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ===== 本地稠密向量（langchain_huggingface，默认 BAAI/bge-m3）=====
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu
DENSE_EMBEDDING_DIM=1024

# ===== Rerank (可选，不配则自动降级) =====
RERANK_MODEL=qwen3-rerank
RERANK_BINDING_HOST=https://dashscope.aliyuncs.com/compatible-api/v1
RERANK_API_KEY=

# ===== Milvus =====
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530
MILVUS_COLLECTION=embeddings_collection

# ===== Database / Cache =====
DATABASE_URL=postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/langchain_app
REDIS_URL=redis://127.0.0.1:6379/0

# ===== Auth =====
JWT_SECRET_KEY=replace-with-strong-random-secret
ADMIN_INVITE_CODE=mindmirror-admin-2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
PASSWORD_PBKDF2_ROUNDS=310000

# ===== BM25 稀疏统计持久化（默认 data/bm25_state.json，可改路径）=====
# BM25_STATE_PATH=/path/to/bm25_state.json

# ===== Tools （可选）=====
AMAP_WEATHER_API=https://restapi.amap.com/v3/weather/weatherInfo
AMAP_API_KEY=your_amap_api_key

```

### 4) Docker 部署（数据库 + 缓存 + 向量库）
当前仓库的 `docker-compose.yml` 同时承载业务依赖与 Milvus 依赖：
- 业务依赖：`postgres`、`redis`
- 向量依赖：`etcd`、`minio`、`standalone`、`attu`

```bash
# 启动向量库依赖
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志（可选）
docker compose logs -f standalone
```

端口说明：
- PostgreSQL：`5432`
- Redis：`6379`
- Milvus：`19530`
- Milvus 健康检查：`9091`
- MinIO API：`9000`
- MinIO Console：`9001`
- Attu：`8080`

### 5) 启动应用并访问
在 Milvus 启动后，运行后端应用：

```bash
uv run uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

浏览器访问：
- 前端页面：`http://127.0.0.1:8000/`
- API 文档：`http://127.0.0.1:8000/docs`
