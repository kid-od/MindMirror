"""聊天与会话路由。"""

try:
    import api_context as ctx
except ModuleNotFoundError:
    from backend import api_context as ctx


router = ctx.APIRouter()


@router.get("/sessions/{session_id}", response_model=ctx.SessionMessagesResponse)
async def get_session_messages(session_id: str, current_user: ctx.User = ctx.Depends(ctx.get_current_user)):
    """获取指定会话的所有消息"""
    try:
        session_meta = ctx.storage.get_session_metadata(current_user.username, session_id)
        messages = [
            ctx.MessageInfo(
                type=msg["type"],
                content=msg["content"],
                timestamp=msg["timestamp"],
                rag_trace=msg.get("rag_trace"),
            )
            for msg in ctx.storage.get_session_messages(current_user.username, session_id)
        ]
        return ctx.SessionMessagesResponse(messages=messages, **session_meta)
    except Exception as e:
        raise ctx.HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=ctx.SessionListResponse)
async def list_sessions(current_user: ctx.User = ctx.Depends(ctx.get_current_user)):
    """获取当前用户的所有会话列表"""
    try:
        sessions = [ctx.SessionInfo(**item) for item in ctx.storage.list_session_infos(current_user.username)]
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return ctx.SessionListResponse(sessions=sessions)
    except Exception as e:
        raise ctx.HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}", response_model=ctx.SessionDeleteResponse)
async def delete_session(session_id: str, current_user: ctx.User = ctx.Depends(ctx.get_current_user)):
    """删除当前用户的指定会话"""
    try:
        deleted = ctx.storage.delete_session(current_user.username, session_id)
        if not deleted:
            raise ctx.HTTPException(status_code=404, detail="会话不存在")
        return ctx.SessionDeleteResponse(session_id=session_id, message="成功删除会话")
    except ctx.HTTPException:
        raise
    except Exception as e:
        raise ctx.HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ctx.ChatResponse)
async def chat_endpoint(request: ctx.ChatRequest, current_user: ctx.User = ctx.Depends(ctx.get_current_user)):
    try:
        session_id = request.session_id or "default_session"
        resp = ctx.chat_with_agent(
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
            return ctx.ChatResponse(**resp)
        return ctx.ChatResponse(response=resp)
    except Exception as e:
        message = ctx.format_model_error_message(e, ctx.BASE_URL)
        code = ctx.extract_model_error_code(str(e))
        if code:
            raise ctx.HTTPException(status_code=code, detail=message)
        raise ctx.HTTPException(status_code=500, detail=message)


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ctx.ChatRequest, current_user: ctx.User = ctx.Depends(ctx.get_current_user)):
    """跟 Agent 对话 (流式)"""

    async def event_generator():
        try:
            session_id = request.session_id or "default_session"
            async for chunk in ctx.chat_with_agent_stream(
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
            error_data = {"type": "error", "content": ctx.format_model_error_message(e, ctx.BASE_URL)}
            yield f"data: {ctx.json.dumps(error_data)}\n\n"

    return ctx.StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
