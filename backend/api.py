"""API router 聚合出口。

历史上业务路由集中在本文件；现在它只暴露 routes 包组装好的 router，
让 app.py 保持稳定，也让测试和旧导入路径继续可用。
"""

try:
    from routes import router
except ModuleNotFoundError:
    from backend.routes import router

__all__ = ["router"]
