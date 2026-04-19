import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from agent import chat_with_agent, chat_with_agent_stream, storage
from auth import authenticate_user, create_access_token, get_current_user, get_db, get_password_hash, require_admin, resolve_role
from document_loader import DocumentLoader
from embedding import embedding_service
try:
    from essay_store import EssayStore
except ModuleNotFoundError:
    from backend.essay_store import EssayStore
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
    LoginRequest,
    MessageInfo,
    RegisterRequest,
    SessionDeleteResponse,
    SessionInfo,
    SessionListResponse,
    SessionMessagesResponse,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
UPLOAD_DIR = DATA_DIR / "documents"
ESSAY_UPLOAD_DIR = DATA_DIR / "essays"
BASE_URL = normalize_base_url(os.getenv("BASE_URL"))
KNOWLEDGE_COLLECTION = os.getenv("MILVUS_KNOWLEDGE_COLLECTION") or os.getenv("MILVUS_COLLECTION", "embeddings_collection")
ESSAY_COLLECTION = os.getenv("MILVUS_ESSAY_COLLECTION", "essay_chunks")


def _create_milvus_manager(collection_name: str) -> MilvusManager:
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

router = APIRouter()


def _escape_filter_value(value: str) -> str:
    return (value or "").replace("\\", "\\\\").replace('"', '\\"')


def _build_scope_metadata(visibility: str, owner_id: str, document_domain: str) -> dict[str, str]:
    return {
        "visibility": visibility,
        "owner_id": owner_id,
        "document_domain": document_domain,
    }


def _build_scoped_filter(filename: str | None, metadata: dict[str, str]) -> str:
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
    os.makedirs(upload_dir, exist_ok=True)
    file_path = upload_dir / filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path, len(content)


def _owner_upload_dir(owner_id: str) -> Path:
    safe_owner = re.sub(r"[^A-Za-z0-9._-]+", "_", (owner_id or "").strip()) or "user"
    return ESSAY_UPLOAD_DIR / safe_owner


def _delete_parent_chunks_for_scope(filename: str, metadata: dict[str, str]) -> None:
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
    try:
        _remove_bm25_stats(knowledge_milvus_manager, delete_expr)
    except Exception:
        pass
    try:
        knowledge_milvus_manager.delete(delete_expr)
    except Exception:
        pass
    try:
        _delete_parent_chunks_for_scope(filename, metadata)
    except Exception:
        pass

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
    try:
        _remove_bm25_stats(essay_milvus_manager, delete_expr)
    except Exception:
        pass
    try:
        essay_milvus_manager.delete(delete_expr)
    except Exception:
        pass
    if legacy_essay_milvus_manager:
        try:
            _remove_bm25_stats(legacy_essay_milvus_manager, delete_expr)
        except Exception:
            pass
        try:
            legacy_essay_milvus_manager.delete(delete_expr)
        except Exception:
            pass
        try:
            _delete_parent_chunks_for_scope(filename, metadata)
        except Exception:
            pass

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
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _attach_upload_file_context(event: dict, filename: str, file_index: int, total_files: int) -> dict:
    enriched = dict(event)
    enriched["filename"] = filename
    enriched["file_index"] = file_index
    enriched["total_files"] = total_files
    if total_files > 1 and enriched.get("detail"):
        enriched["detail"] = f"[{file_index}/{total_files}] {filename}：{enriched['detail']}"
    return enriched


def _build_batch_upload_message(successes: list[dict[str, Any]], failures: list[dict[str, Any]], total_files: int) -> str:
    if total_files == 1 and successes and not failures:
        return successes[0].get("message", "文档上传完成")
    message = f"批量上传完成：成功 {len(successes)} 个，失败 {len(failures)} 个"
    if not successes and failures:
        details = "；".join(f"{item.get('filename', '未知文件')}：{item.get('content', '上传失败')}" for item in failures)
        return f"{message}。{details}"
    return message


@router.post("/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    username = (request.username or "").strip()
    password = (request.password or "").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    exists = db.query(User).filter(User.username == username).first()
    if exists:
        raise HTTPException(status_code=409, detail="用户名已存在")

    role = resolve_role(request.role, request.admin_code)
    user = User(username=username, password_hash=get_password_hash(password), role=role)
    db.add(user)
    db.commit()

    token = create_access_token(username=username, role=role)
    return AuthResponse(access_token=token, username=username, role=role)


@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(username=user.username, role=user.role)
    return AuthResponse(access_token=token, username=user.username, role=user.role)


@router.get("/auth/me", response_model=CurrentUserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return CurrentUserResponse(username=current_user.username, role=current_user.role)


@router.get("/daily-quote", response_model=DailyQuoteResponse)
async def daily_quote(
    locale: str = Query(default="zh", pattern="^(zh|en)$"),
    _: User = Depends(get_current_user),
):
    try:
        return DailyQuoteResponse(**get_daily_quote(locale))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取每日一句失败: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SessionMessagesResponse)
async def get_session_messages(session_id: str, current_user: User = Depends(get_current_user)):
    """获取指定会话的所有消息"""
    try:
        session_meta = storage.get_session_metadata(current_user.username, session_id)
        messages = [
            MessageInfo(
                type=msg["type"],
                content=msg["content"],
                timestamp=msg["timestamp"],
                rag_trace=msg.get("rag_trace"),
            )
            for msg in storage.get_session_messages(current_user.username, session_id)
        ]
        return SessionMessagesResponse(messages=messages, **session_meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(current_user: User = Depends(get_current_user)):
    """获取当前用户的所有会话列表"""
    try:
        sessions = [SessionInfo(**item) for item in storage.list_session_infos(current_user.username)]
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return SessionListResponse(sessions=sessions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(session_id: str, current_user: User = Depends(get_current_user)):
    """删除当前用户的指定会话"""
    try:
        deleted = storage.delete_session(current_user.username, session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="会话不存在")
        return SessionDeleteResponse(session_id=session_id, message="成功删除会话")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: User = Depends(get_current_user)):
    try:
        session_id = request.session_id or "default_session"
        resp = chat_with_agent(
            request.message,
            current_user.username,
            session_id,
            session_context={
                "active_essay_id": request.active_essay_id,
                "active_essay_title": request.active_essay_title,
                "analysis_mode": request.analysis_mode,
            },
        )
        if isinstance(resp, dict):
            return ChatResponse(**resp)
        return ChatResponse(response=resp)
    except Exception as e:
        message = format_model_error_message(e, BASE_URL)
        code = extract_model_error_code(str(e))
        if code:
            raise HTTPException(status_code=code, detail=message)
        raise HTTPException(status_code=500, detail=message)


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """跟 Agent 对话 (流式)"""

    async def event_generator():
        try:
            session_id = request.session_id or "default_session"
            async for chunk in chat_with_agent_stream(
                request.message,
                current_user.username,
                session_id,
                session_context={
                    "active_essay_id": request.active_essay_id,
                    "active_essay_title": request.active_essay_title,
                    "analysis_mode": request.analysis_mode,
                },
            ):
                yield chunk
        except Exception as e:
            error_data = {"type": "error", "content": format_model_error_message(e, BASE_URL)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/essays", response_model=EssayListResponse)
async def list_essays(current_user: User = Depends(get_current_user)):
    """获取当前用户的私密随笔列表。"""
    try:
        file_stats: dict[str, dict[str, Any]] = {}
        for item in essay_store.list_by_owner(current_user.username):
            file_stats[item.get("filename", "")] = {
                "essay_id": item.get("essay_id"),
                "title": item.get("title"),
                "filename": item.get("filename", ""),
                "file_type": item.get("file_type", ""),
                "language": item.get("language"),
                "chunk_count": int(item.get("chunk_count") or 0),
                "uploaded_at": item.get("updated_at"),
            }
        if legacy_essay_milvus_manager:
            try:
                legacy_essay_milvus_manager.init_collection()
                legacy_rows = legacy_essay_milvus_manager.query_all(
                    filter_expr=_private_essay_filter(filename=None, owner_id=current_user.username),
                    output_fields=["filename", "file_type"],
                )
                for row in legacy_rows:
                    filename = row.get("filename", "")
                    if not filename:
                        continue
                    existing = file_stats.get(filename)
                    if not existing:
                        file_stats[filename] = {
                            "essay_id": None,
                            "title": Path(filename).stem,
                            "filename": filename,
                            "file_type": row.get("file_type", ""),
                            "language": None,
                            "chunk_count": 0,
                            "uploaded_at": None,
                        }
                    file_stats[filename]["chunk_count"] = int(file_stats[filename].get("chunk_count") or 0) + 1
            except Exception:
                pass
        essays = [EssayInfo(**stats) for _, stats in sorted(file_stats.items(), key=lambda pair: pair[0].lower())]
        return EssayListResponse(essays=essays)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取随笔列表失败: {str(e)}")


@router.post("/essays/upload/stream")
async def upload_essay_stream(
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user),
):
    """上传当前用户的私密随笔并返回实时进度。"""

    async def event_generator():
        try:
            upload_files = collect_upload_files(file=file, files=files)
            if not upload_files:
                raise HTTPException(status_code=400, detail="请选择至少一个文件")

            total_files = len(upload_files)
            successes: list[dict[str, Any]] = []
            failures: list[dict[str, Any]] = []
            metadata = {
                "visibility": "private",
                "owner_id": current_user.username,
                "document_domain": "essay",
            }
            upload_dir = _owner_upload_dir(current_user.username)

            for file_index, upload_file in enumerate(upload_files, 1):
                filename = upload_file.filename or ""
                try:
                    _validate_upload_filename(filename)
                    yield _sse_payload(
                        _attach_upload_file_context(
                            build_upload_progress_event("uploading", detail=f"正在接收 {filename}"),
                            filename,
                            file_index,
                            total_files,
                        )
                    )

                    file_path, file_size = await _save_uploaded_file(upload_file, filename, upload_dir=upload_dir)
                    yield _sse_payload(
                        _attach_upload_file_context(
                            build_upload_progress_event(
                                "uploading",
                                detail=f"{filename} 已接收完成（{_format_file_size(file_size)}）",
                                state="completed",
                            ),
                            filename,
                            file_index,
                            total_files,
                        )
                    )

                    output_queue = asyncio.Queue()
                    loop = asyncio.get_running_loop()

                    def progress_callback(event: dict) -> None:
                        loop.call_soon_threadsafe(
                            output_queue.put_nowait,
                            _attach_upload_file_context(event, filename, file_index, total_files),
                        )

                    async def worker():
                        try:
                            result = await asyncio.to_thread(
                                _process_uploaded_essay_sync,
                                filename,
                                file_path,
                                current_user.username,
                                progress_callback,
                            )
                            await output_queue.put(
                                {
                                    "type": "file_success",
                                    "filename": result.filename,
                                    "file_index": file_index,
                                    "total_files": total_files,
                                    "chunks_processed": result.chunks_processed,
                                    "message": result.message,
                                }
                            )
                        except HTTPException as exc:
                            await output_queue.put(
                                {
                                    "type": "file_error",
                                    "filename": filename,
                                    "file_index": file_index,
                                    "total_files": total_files,
                                    "content": exc.detail,
                                }
                            )
                        except Exception as exc:
                            await output_queue.put(
                                {
                                    "type": "file_error",
                                    "filename": filename,
                                    "file_index": file_index,
                                    "total_files": total_files,
                                    "content": f"随笔上传失败: {exc}",
                                }
                            )
                        finally:
                            await output_queue.put(None)

                    worker_task = asyncio.create_task(worker())
                    while True:
                        event = await output_queue.get()
                        if event is None:
                            break
                        if event.get("type") == "file_success":
                            successes.append(event)
                        elif event.get("type") == "file_error":
                            failures.append(event)
                        yield _sse_payload(event)
                    await worker_task
                except HTTPException as exc:
                    failure = {
                        "type": "file_error",
                        "filename": filename or "未知文件",
                        "file_index": file_index,
                        "total_files": total_files,
                        "content": exc.detail,
                    }
                    failures.append(failure)
                    yield _sse_payload(failure)

            summary = {
                "type": "success" if successes else "error",
                "success_count": len(successes),
                "failure_count": len(failures),
                "total_files": total_files,
                "files": successes,
                "failures": failures,
            }
            message = _build_batch_upload_message(successes, failures, total_files)
            if successes:
                summary["message"] = message
            else:
                summary["content"] = message
            yield _sse_payload(summary)
        except HTTPException as exc:
            yield _sse_payload({"type": "error", "content": exc.detail})
        except Exception as exc:
            yield _sse_payload({"type": "error", "content": f"随笔上传失败: {exc}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(_: User = Depends(require_admin)):
    """获取已上传的文档列表（管理员）"""
    try:
        knowledge_milvus_manager.init_collection()

        results = knowledge_milvus_manager.query_all(
            filter_expr=_public_document_filter(),
            output_fields=["filename", "file_type"],
        )

        file_stats: dict[str, dict[str, Any]] = {}
        for item in results:
            filename = item.get("filename", "")
            file_type = item.get("file_type", "")
            if filename not in file_stats:
                file_stats[filename] = {
                    "filename": filename,
                    "file_type": file_type,
                    "chunk_count": 0,
                }
            file_stats[filename]["chunk_count"] += 1

        documents = [DocumentInfo(**stats) for _, stats in sorted(file_stats.items(), key=lambda pair: pair[0].lower())]
        return DocumentListResponse(documents=documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.delete("/essays/{filename}", response_model=EssayDeleteResponse)
async def delete_essay(filename: str, current_user: User = Depends(get_current_user)):
    """删除当前用户私密随笔的向量和父级分块。"""
    try:
        essay_milvus_manager.init_collection()
        filter_expr = _private_essay_filter(filename=filename, owner_id=current_user.username)
        try:
            _remove_bm25_stats(essay_milvus_manager, filter_expr)
        except Exception:
            pass
        result = essay_milvus_manager.delete(filter_expr)
        if legacy_essay_milvus_manager:
            try:
                _remove_bm25_stats(legacy_essay_milvus_manager, filter_expr)
            except Exception:
                pass
            try:
                legacy_essay_milvus_manager.delete(filter_expr)
            except Exception:
                pass
            try:
                _delete_parent_chunks_for_scope(
                    filename,
                    {
                        "visibility": "private",
                        "owner_id": current_user.username,
                        "document_domain": "essay",
                    },
                )
            except Exception:
                pass
        essay_store.delete(current_user.username, filename)
        file_path = _owner_upload_dir(current_user.username) / filename
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass

        return EssayDeleteResponse(
            filename=filename,
            chunks_deleted=result.get("delete_count", 0) if isinstance(result, dict) else 0,
            message=f"成功删除随笔 {filename} 的私密索引",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除随笔失败: {str(e)}")


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), _: User = Depends(require_admin)):
    """上传文档并进行 embedding（管理员）"""
    try:
        filename = file.filename or ""
        _validate_upload_filename(filename)
        file_path, _ = await _save_uploaded_file(file, filename)
        return await asyncio.to_thread(_process_uploaded_document_sync, filename, file_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.post("/documents/upload/stream")
async def upload_document_stream(
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
    _: User = Depends(require_admin),
):
    """上传文档并返回实时进度（管理员）"""

    async def event_generator():
        try:
            upload_files = collect_upload_files(file=file, files=files)
            if not upload_files:
                raise HTTPException(status_code=400, detail="请选择至少一个文件")

            total_files = len(upload_files)
            successes: list[dict[str, Any]] = []
            failures: list[dict[str, Any]] = []

            for file_index, upload_file in enumerate(upload_files, 1):
                filename = upload_file.filename or ""
                try:
                    _validate_upload_filename(filename)
                    yield _sse_payload(
                        _attach_upload_file_context(
                            build_upload_progress_event("uploading", detail=f"正在接收 {filename}"),
                            filename,
                            file_index,
                            total_files,
                        )
                    )

                    file_path, file_size = await _save_uploaded_file(upload_file, filename)
                    yield _sse_payload(
                        _attach_upload_file_context(
                            build_upload_progress_event(
                                "uploading",
                                detail=f"{filename} 已接收完成（{_format_file_size(file_size)}）",
                                state="completed",
                            ),
                            filename,
                            file_index,
                            total_files,
                        )
                    )

                    output_queue = asyncio.Queue()
                    loop = asyncio.get_running_loop()

                    def progress_callback(event: dict) -> None:
                        loop.call_soon_threadsafe(
                            output_queue.put_nowait,
                            _attach_upload_file_context(event, filename, file_index, total_files),
                        )

                    async def worker():
                        try:
                            result = await asyncio.to_thread(
                                _process_uploaded_document_sync,
                                filename,
                                file_path,
                                progress_callback,
                            )
                            await output_queue.put(
                                {
                                    "type": "file_success",
                                    "filename": result.filename,
                                    "file_index": file_index,
                                    "total_files": total_files,
                                    "chunks_processed": result.chunks_processed,
                                    "message": result.message,
                                }
                            )
                        except HTTPException as exc:
                            await output_queue.put(
                                {
                                    "type": "file_error",
                                    "filename": filename,
                                    "file_index": file_index,
                                    "total_files": total_files,
                                    "content": exc.detail,
                                }
                            )
                        except Exception as exc:
                            await output_queue.put(
                                {
                                    "type": "file_error",
                                    "filename": filename,
                                    "file_index": file_index,
                                    "total_files": total_files,
                                    "content": f"文档上传失败: {exc}",
                                }
                            )
                        finally:
                            await output_queue.put(None)

                    worker_task = asyncio.create_task(worker())
                    while True:
                        event = await output_queue.get()
                        if event is None:
                            break
                        if event.get("type") == "file_success":
                            successes.append(event)
                        elif event.get("type") == "file_error":
                            failures.append(event)
                        yield _sse_payload(event)
                    await worker_task
                except HTTPException as exc:
                    failure = {
                        "type": "file_error",
                        "filename": filename or "未知文件",
                        "file_index": file_index,
                        "total_files": total_files,
                        "content": exc.detail,
                    }
                    failures.append(failure)
                    yield _sse_payload(failure)

            summary = {
                "type": "success" if successes else "error",
                "success_count": len(successes),
                "failure_count": len(failures),
                "total_files": total_files,
                "files": successes,
                "failures": failures,
            }
            message = _build_batch_upload_message(successes, failures, total_files)
            if successes:
                summary["message"] = message
            else:
                summary["content"] = message
            yield _sse_payload(summary)
        except HTTPException as exc:
            yield _sse_payload({"type": "error", "content": exc.detail})
        except Exception as exc:
            yield _sse_payload({"type": "error", "content": f"文档上传失败: {exc}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/documents/{filename}", response_model=DocumentDeleteResponse)
async def delete_document(filename: str, _: User = Depends(require_admin)):
    """删除文档在 Milvus 中的向量（保留本地文件，管理员）"""
    try:
        knowledge_milvus_manager.init_collection()

        delete_expr = _public_document_filter(filename)
        _remove_bm25_stats(knowledge_milvus_manager, delete_expr)
        result = knowledge_milvus_manager.delete(delete_expr)
        _delete_parent_chunks_for_scope(filename, _build_scope_metadata("public", "", "knowledge_base"))

        return DocumentDeleteResponse(
            filename=filename,
            chunks_deleted=result.get("delete_count", 0) if isinstance(result, dict) else 0,
            message=f"成功删除文档 {filename} 的向量数据（本地文件已保留）",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")
