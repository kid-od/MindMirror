"""路由层共享上下文。

routes/* 只描述 HTTP 端点；这里集中放置依赖实例、路径常量、上传处理、
Milvus 作用域过滤和 SSE 小工具，避免每个路由模块重复创建重量级对象。
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from agent import chat_with_agent, chat_with_agent_stream, storage
from auth import authenticate_user, create_access_token, get_current_user, get_db, get_password_hash, require_admin, resolve_role
from document_loader import DocumentLoader
from embedding import embedding_service
try:
    from activity_views import build_insights_payload, build_timeline_payload, list_public_document_activity
except ModuleNotFoundError:
    from backend.activity_views import build_insights_payload, build_timeline_payload, list_public_document_activity
try:
    from essay_store import EssayStore
except ModuleNotFoundError:
    from backend.essay_store import EssayStore
try:
    from document_previews import build_cover_url, delete_document_cover, ensure_document_cover, preview_cache_path
except ModuleNotFoundError as exc:
    if exc.name != "document_previews":
        raise
    from backend.document_previews import build_cover_url, delete_document_cover, ensure_document_cover, preview_cache_path
from milvus_client import MilvusManager
from milvus_writer import MilvusWriter
from models import User
from parent_chunk_store import ParentChunkStore
from config import normalize_base_url
from daily_quote import get_daily_quote
from error_utils import extract_model_error_code, format_model_error_message
from service_checks import ensure_tcp_service
from upload_progress import build_upload_progress_event
try:
    from upload_files import collect_upload_files, validate_upload_filename
except ModuleNotFoundError:
    from backend.upload_files import collect_upload_files, validate_upload_filename
from schemas import (
    AuthResponse,
    ChatRequest,
    ChatResponse,
    CurrentUserResponse,
    DailyQuoteResponse,
    DocumentDeleteResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentUploadResponse,
    EssayDeleteResponse,
    EssayInfo,
    EssayListResponse,
    InsightsResponse,
    LoginRequest,
    MessageInfo,
    RegisterRequest,
    SessionDeleteResponse,
    SessionInfo,
    SessionListResponse,
    SessionMessagesResponse,
    TimelineResponse,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
UPLOAD_DIR = DATA_DIR / "documents"
ESSAY_UPLOAD_DIR = DATA_DIR / "essays"
BASE_URL = normalize_base_url(os.getenv("BASE_URL"))
KNOWLEDGE_COLLECTION = os.getenv("MILVUS_KNOWLEDGE_COLLECTION") or os.getenv("MILVUS_COLLECTION", "embeddings_collection")
ESSAY_COLLECTION = os.getenv("MILVUS_ESSAY_COLLECTION", "essay_chunks")


def _create_milvus_manager(collection_name: str) -> MilvusManager:
    """兼容测试替身和真实 MilvusManager 的构造签名。"""
    try:
        return MilvusManager(collection_name=collection_name)
    except TypeError:
        return MilvusManager()

loader = DocumentLoader()
parent_chunk_store = ParentChunkStore()
essay_store = EssayStore()
knowledge_milvus_manager = _create_milvus_manager(KNOWLEDGE_COLLECTION)
essay_milvus_manager = _create_milvus_manager(ESSAY_COLLECTION)
legacy_essay_milvus_manager = None if ESSAY_COLLECTION == KNOWLEDGE_COLLECTION else _create_milvus_manager(KNOWLEDGE_COLLECTION)
milvus_manager = knowledge_milvus_manager
milvus_writer = MilvusWriter(embedding_service=embedding_service, milvus_manager=knowledge_milvus_manager)
essay_milvus_writer = MilvusWriter(embedding_service=embedding_service, milvus_manager=essay_milvus_manager)

def _escape_filter_value(value: str) -> str:
    """转义 Milvus filter 字符串中的反斜线和双引号。"""
    return (value or "").replace("\\", "\\\\").replace('"', '\\"')


def _build_scope_metadata(visibility: str, owner_id: str, document_domain: str) -> dict[str, str]:
    """构造写入 chunk 时随身携带的访问作用域。"""
    return {
        "visibility": visibility,
        "owner_id": owner_id,
        "document_domain": document_domain,
    }


def _build_scoped_filter(filename: str | None, metadata: dict[str, str]) -> str:
    """把访问作用域翻译成 Milvus filter，保证公共资料和私密随笔不会串库。"""
    clauses = [
        f'visibility == "{_escape_filter_value(metadata.get("visibility", "public"))}"',
        f'owner_id == "{_escape_filter_value(metadata.get("owner_id", ""))}"',
        f'document_domain == "{_escape_filter_value(metadata.get("document_domain", "knowledge_base"))}"',
    ]
    if filename:
        clauses.append(f'filename == "{_escape_filter_value(filename)}"')
    return " and ".join(clauses)


def _private_essay_filter(filename: str | None, owner_id: str) -> str:
    return _build_scoped_filter(
        filename=filename,
        metadata=_build_scope_metadata("private", owner_id, "essay"),
    )


def _public_document_filter(filename: str | None = None) -> str:
    return _build_scoped_filter(
        filename=filename,
        metadata=_build_scope_metadata("public", "", "knowledge_base"),
    )


def _remove_bm25_stats(manager: MilvusManager, filter_expr: str) -> None:
    """删除 Milvus 中指定作用域 chunk 前，先从持久化 BM25 统计中扣减。"""
    rows = manager.query_all(
        filter_expr=filter_expr,
        output_fields=["text"],
    )
    texts = [r.get("text") or "" for r in rows]
    embedding_service.increment_remove_documents(texts)


def _best_effort_cleanup(action) -> None:
    """上传同名文件时先清理旧索引；清理失败不阻断后续重新解析和写入。"""
    try:
        action()
    except Exception:
        pass


def _validate_upload_filename(filename: str) -> str:
    try:
        return validate_upload_filename(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _format_file_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(num_bytes)
    unit = units[0]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            break
        value /= 1024
    if unit == "B":
        return f"{int(value)} {unit}"
    return f"{value:.1f} {unit}"


async def _save_uploaded_file(file: UploadFile, filename: str, upload_dir: Path = UPLOAD_DIR) -> tuple[Path, int]:
    """将 UploadFile 落盘，并返回保存路径和原始字节数。"""
    os.makedirs(upload_dir, exist_ok=True)
    file_path = upload_dir / filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path, len(content)


def _owner_upload_dir(owner_id: str) -> Path:
    """为用户私密随笔生成隔离目录，避免用户名中的特殊字符影响路径。"""
    safe_owner = re.sub(r"[^A-Za-z0-9._-]+", "_", (owner_id or "").strip()) or "user"
    return ESSAY_UPLOAD_DIR / safe_owner


def _delete_parent_chunks_for_scope(filename: str, metadata: dict[str, str]) -> None:
    """删除 PostgreSQL 中与 Milvus 同作用域的父级 chunk。"""
    try:
        parent_chunk_store.delete_by_filename_and_scope(
            filename=filename,
            visibility=metadata.get("visibility", "public"),
            owner_id=metadata.get("owner_id", ""),
            document_domain=metadata.get("document_domain", "knowledge_base"),
        )
    except AttributeError:
        if metadata.get("visibility") == "private":
            parent_chunk_store.delete_by_filename_and_owner(filename, metadata.get("owner_id", ""))
        else:
            parent_chunk_store.delete_by_filename(filename)


def _process_uploaded_document_sync(
    filename: str,
    file_path: Path,
    progress_callback=None,
    metadata: dict[str, Any] | None = None,
) -> DocumentUploadResponse:
    """处理公共知识库文件：解析、三层分块、写父块、写 Milvus 叶子块。"""
    metadata = metadata or _build_scope_metadata("public", "", "knowledge_base")

    def emit(stage: str, detail: str, state: str = "running") -> None:
        if progress_callback:
            progress_callback(build_upload_progress_event(stage, detail=detail, state=state))

    try:
        ensure_tcp_service(knowledge_milvus_manager.host, int(knowledge_milvus_manager.port), "Milvus")
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"{exc} 请先执行 `docker compose up -d` 启动向量库依赖。",
        )

    knowledge_milvus_manager.init_collection()

    delete_expr = _build_scoped_filter(filename, metadata)
    emit("parsing", f"正在解析 {filename}")
    _best_effort_cleanup(lambda: _remove_bm25_stats(knowledge_milvus_manager, delete_expr))
    _best_effort_cleanup(lambda: knowledge_milvus_manager.delete(delete_expr))
    _best_effort_cleanup(lambda: _delete_parent_chunks_for_scope(filename, metadata))

    try:
        new_docs = loader.load_document(str(file_path), filename, metadata=metadata)
    except Exception as doc_err:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {doc_err}")

    if not new_docs:
        raise HTTPException(status_code=500, detail="文档处理失败，未能提取内容")
    emit("parsing", f"文档解析完成，共提取 {len(new_docs)} 个原始分块", state="completed")

    emit("chunking", "正在整理父级分块与叶子分块")
    parent_docs = [doc for doc in new_docs if int(doc.get("chunk_level", 0) or 0) in (1, 2)]
    leaf_docs = [doc for doc in new_docs if int(doc.get("chunk_level", 0) or 0) == 3]
    if not leaf_docs:
        raise HTTPException(status_code=500, detail="文档处理失败，未生成可检索叶子分块")
    emit(
        "chunking",
        f"叶子分块 {len(leaf_docs)} 个，父级分块 {len(parent_docs)} 个",
        state="completed",
    )

    parent_chunk_store.upsert_documents(parent_docs)
    milvus_writer.write_documents(leaf_docs, progress_callback=progress_callback)
    ensure_document_cover(file_path, filename, metadata.get("file_type", new_docs[0].get("file_type", "")), DATA_DIR)

    emit("indexing", "正在整理索引并提交结果")
    emit("indexing", f"知识库写入完成，共 {len(leaf_docs)} 个叶子分块", state="completed")

    return DocumentUploadResponse(
        filename=filename,
        chunks_processed=len(leaf_docs),
        message=(
            f"成功上传并处理 {filename}，叶子分块 {len(leaf_docs)} 个，"
            f"父级分块 {len(parent_docs)} 个（存入 PostgreSQL）"
        ),
    )


def _process_uploaded_essay_sync(
    filename: str,
    file_path: Path,
    owner_id: str,
    progress_callback=None,
) -> DocumentUploadResponse:
    """处理用户私密随笔：保存正文、生成私密 chunk、写入独立 essay collection。"""
    metadata = _build_scope_metadata("private", owner_id, "essay")

    def emit(stage: str, detail: str, state: str = "running") -> None:
        if progress_callback:
            progress_callback(build_upload_progress_event(stage, detail=detail, state=state))

    try:
        ensure_tcp_service(essay_milvus_manager.host, int(essay_milvus_manager.port), "Milvus")
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"{exc} 请先执行 `docker compose up -d` 启动向量库依赖。",
        )

    essay_milvus_manager.init_collection()
    delete_expr = _private_essay_filter(filename, owner_id)
    emit("parsing", f"正在解析 {filename}")
    _best_effort_cleanup(lambda: _remove_bm25_stats(essay_milvus_manager, delete_expr))
    _best_effort_cleanup(lambda: essay_milvus_manager.delete(delete_expr))
    if legacy_essay_milvus_manager:
        _best_effort_cleanup(lambda: _remove_bm25_stats(legacy_essay_milvus_manager, delete_expr))
        _best_effort_cleanup(lambda: legacy_essay_milvus_manager.delete(delete_expr))
        _best_effort_cleanup(lambda: _delete_parent_chunks_for_scope(filename, metadata))

    try:
        essay_payload = loader.load_essay_document(str(file_path), filename, metadata=metadata)
    except Exception as doc_err:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {doc_err}")

    content = (essay_payload.get("content") or "").strip()
    essay_chunks = essay_payload.get("chunks") or []
    if not content or not essay_chunks:
        raise HTTPException(status_code=500, detail="随笔处理失败，未能提取正文")

    emit("parsing", f"随笔解析完成，正文长度 {len(content)} 字", state="completed")
    emit("chunking", f"正在整理随笔分块，共 {len(essay_chunks)} 个")
    essay_record = essay_store.upsert(
        owner_id=owner_id,
        filename=filename,
        content=content,
        file_type=essay_payload.get("file_type", ""),
        file_path=str(file_path),
        chunk_count=len(essay_chunks),
    )
    emit("chunking", f"随笔正文已入库，标题《{essay_record.get('title', filename)}》", state="completed")
    essay_milvus_writer.write_documents(essay_chunks, progress_callback=progress_callback)
    emit("indexing", f"随笔索引完成，共 {len(essay_chunks)} 个检索分块", state="completed")

    return DocumentUploadResponse(
        filename=filename,
        chunks_processed=len(essay_chunks),
        message=f"成功上传随笔 {filename}，正文已保存并建立 {len(essay_chunks)} 个检索分块",
    )


def _sse_payload(data: dict) -> str:
    """把事件 dict 包装成浏览器 EventSource / fetch reader 能识别的 SSE 行。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _attach_upload_file_context(event: dict, filename: str, file_index: int, total_files: int) -> dict:
    """给单文件进度事件补上批量上传上下文，前端可直接展示第几个文件。"""
    enriched = dict(event)
    enriched["filename"] = filename
    enriched["file_index"] = file_index
    enriched["total_files"] = total_files
    if total_files > 1 and enriched.get("detail"):
        enriched["detail"] = f"[{file_index}/{total_files}] {filename}：{enriched['detail']}"
    return enriched


def _build_batch_upload_message(successes: list[dict[str, Any]], failures: list[dict[str, Any]], total_files: int) -> str:
    """根据批量上传结果生成最终提示文案。"""
    if total_files == 1 and successes and not failures:
        return successes[0].get("message", "文档上传完成")
    message = f"批量上传完成：成功 {len(successes)} 个，失败 {len(failures)} 个"
    if not successes and failures:
        details = "；".join(f"{item.get('filename', '未知文件')}：{item.get('content', '上传失败')}" for item in failures)
        return f"{message}。{details}"
    return message
