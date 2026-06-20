"""按业务领域聚合 FastAPI routers。"""

from fastapi import APIRouter

from . import activity, auth, chat, documents, essays

router = APIRouter()

for domain_router in (
    auth.router,
    activity.router,
    chat.router,
    essays.router,
    documents.router,
):
    router.include_router(domain_router)
