"""FastAPI 应用入口。

本文件只负责组装应用：初始化数据库、挂载 CORS / 静态文件、接入聚合后的 API router。
具体业务逻辑按领域拆在 backend/routes/*，方便从入口一路追到各功能模块。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sys

import api as api_module
from config import parse_cors_origins
from database import init_db

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def create_app() -> FastAPI:
    """创建可被 uvicorn、测试用例和命令行入口复用的 FastAPI 实例。"""
    app = FastAPI(title="MindMirror API")

    @app.on_event("startup")
    async def _startup_init_db():
        init_db()

    cors_origins = parse_cors_origins(os.getenv("CORS_ORIGINS"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials="*" not in cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 开发环境避免浏览器缓存前端资源，改 CSS/JS 后刷新即可看到新版本。
    @app.middleware("http")
    async def _no_cache(request, call_next):
        response = await call_next(request)
        path = request.url.path or ""
        if path == "/" or path.endswith((".html", ".js", ".css")):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    app.include_router(api_module.router)

    # 根路径托管 Vue CDN 单页应用；API router 需要先 include，避免被静态资源兜底吞掉。
    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    if "--reload" in sys.argv:
        uvicorn.run("app:app", host=host, port=port, reload=True, app_dir=str(BASE_DIR / "backend"))
    else:
        uvicorn.run(app, host=host, port=port)
