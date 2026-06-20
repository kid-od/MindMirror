"""私密随笔路由。

随笔按当前登录用户隔离：正文写 PostgreSQL，检索 chunk 写 essay collection，
删除时同时清理向量索引、本地文件和随笔正文记录。
"""

try:
    from api_context import (
        APIRouter,
        Any,
        Depends,
        EssayDeleteResponse,
        EssayInfo,
        EssayListResponse,
        File,
        HTTPException,
        Path,
        StreamingResponse,
        UploadFile,
        User,
        _attach_upload_file_context,
        _build_batch_upload_message,
        _delete_parent_chunks_for_scope,
        _format_file_size,
        _owner_upload_dir,
        _private_essay_filter,
        _process_uploaded_essay_sync,
        _remove_bm25_stats,
        _save_uploaded_file,
        _sse_payload,
        _validate_upload_filename,
        asyncio,
        build_upload_progress_event,
        collect_upload_files,
        essay_milvus_manager,
        essay_store,
        get_current_user,
        legacy_essay_milvus_manager,
    )
except ModuleNotFoundError:
    from backend.api_context import (
        APIRouter,
        Any,
        Depends,
        EssayDeleteResponse,
        EssayInfo,
        EssayListResponse,
        File,
        HTTPException,
        Path,
        StreamingResponse,
        UploadFile,
        User,
        _attach_upload_file_context,
        _build_batch_upload_message,
        _delete_parent_chunks_for_scope,
        _format_file_size,
        _owner_upload_dir,
        _private_essay_filter,
        _process_uploaded_essay_sync,
        _remove_bm25_stats,
        _save_uploaded_file,
        _sse_payload,
        _validate_upload_filename,
        asyncio,
        build_upload_progress_event,
        collect_upload_files,
        essay_milvus_manager,
        essay_store,
        get_current_user,
        legacy_essay_milvus_manager,
    )


router = APIRouter()


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
                    filename = _validate_upload_filename(filename)
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
