"""公共知识库文档路由。

这些接口只允许管理员访问，负责上传公共资料、列出已索引文档、
生成封面预览，以及删除对应向量索引。
"""

try:
    from api_context import (
        APIRouter,
        Any,
        DATA_DIR,
        Depends,
        DocumentDeleteResponse,
        DocumentInfo,
        DocumentListResponse,
        DocumentUploadResponse,
        File,
        FileResponse,
        HTTPException,
        Query,
        StreamingResponse,
        UPLOAD_DIR,
        UploadFile,
        User,
        _attach_upload_file_context,
        _build_batch_upload_message,
        _build_scope_metadata,
        _delete_parent_chunks_for_scope,
        _format_file_size,
        _process_uploaded_document_sync,
        _public_document_filter,
        _remove_bm25_stats,
        _save_uploaded_file,
        _sse_payload,
        _validate_upload_filename,
        asyncio,
        build_cover_url,
        build_upload_progress_event,
        collect_upload_files,
        datetime,
        delete_document_cover,
        ensure_document_cover,
        knowledge_milvus_manager,
        preview_cache_path,
        require_admin,
    )
except ModuleNotFoundError:
    from backend.api_context import (
        APIRouter,
        Any,
        DATA_DIR,
        Depends,
        DocumentDeleteResponse,
        DocumentInfo,
        DocumentListResponse,
        DocumentUploadResponse,
        File,
        FileResponse,
        HTTPException,
        Query,
        StreamingResponse,
        UPLOAD_DIR,
        UploadFile,
        User,
        _attach_upload_file_context,
        _build_batch_upload_message,
        _build_scope_metadata,
        _delete_parent_chunks_for_scope,
        _format_file_size,
        _process_uploaded_document_sync,
        _public_document_filter,
        _remove_bm25_stats,
        _save_uploaded_file,
        _sse_payload,
        _validate_upload_filename,
        asyncio,
        build_cover_url,
        build_upload_progress_event,
        collect_upload_files,
        datetime,
        delete_document_cover,
        ensure_document_cover,
        knowledge_milvus_manager,
        preview_cache_path,
        require_admin,
    )


router = APIRouter()


@router.get("/document-cover")
async def get_document_cover(filename: str = Query(...), _: User = Depends(require_admin)):
    try:
        filename = _validate_upload_filename(filename)
        cover_path = preview_cache_path(filename, DATA_DIR)
        if not cover_path.exists():
            source_path = UPLOAD_DIR / filename
            if not source_path.exists():
                raise HTTPException(status_code=404, detail="文档封面不存在")
            cover_path = ensure_document_cover(source_path, filename, source_path.suffix.lstrip(".").upper(), DATA_DIR)
        if not cover_path or not cover_path.exists():
            raise HTTPException(status_code=404, detail="文档封面不存在")
        return FileResponse(cover_path, media_type="image/png")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取文档封面失败: {exc}") from exc


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

        documents: list[DocumentInfo] = []
        for _, stats in sorted(file_stats.items(), key=lambda pair: pair[0].lower()):
            filename = stats.get("filename", "")
            source_path = UPLOAD_DIR / filename
            if source_path.exists():
                stats["uploaded_at"] = datetime.fromtimestamp(source_path.stat().st_mtime).isoformat()
                cover_path = ensure_document_cover(source_path, filename, stats.get("file_type", ""), DATA_DIR)
            else:
                cover_path = preview_cache_path(filename, DATA_DIR)

            if cover_path and cover_path.exists():
                stats["cover_url"] = build_cover_url(filename, int(cover_path.stat().st_mtime))
            else:
                stats["cover_url"] = None

            documents.append(DocumentInfo(**stats))
        return DocumentListResponse(documents=documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), _: User = Depends(require_admin)):
    """上传文档并进行 embedding（管理员）"""
    try:
        filename = file.filename or ""
        filename = _validate_upload_filename(filename)
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
                    filename = _validate_upload_filename(filename)
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
        delete_document_cover(filename, DATA_DIR)

        return DocumentDeleteResponse(
            filename=filename,
            chunks_deleted=result.get("delete_count", 0) if isinstance(result, dict) else 0,
            message=f"成功删除文档 {filename} 的向量数据（本地文件已保留）",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")
