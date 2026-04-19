from dotenv import load_dotenv
import os
import json
import asyncio
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, SystemMessage
from config import normalize_base_url
from error_utils import format_model_error_message
from tools import (
    get_current_weather,
    search_knowledge_base,
    get_last_rag_context,
    reset_tool_call_guards,
    set_current_rag_user,
    set_current_rag_session_context,
    set_rag_step_queue,
)
from datetime import datetime
from cache import cache
from database import SessionLocal
from models import User, ChatSession, ChatMessage
from session_titles import derive_session_title

load_dotenv()

_agent = None
_model = None


def _current_model_settings() -> tuple[str | None, str | None, str | None]:
    api_key = os.getenv("ARK_API_KEY")
    model = os.getenv("MODEL")
    base_url = normalize_base_url(os.getenv("BASE_URL"))
    return api_key, model, base_url


def _missing_model_configuration_message() -> str:
    api_key, model, _base_url = _current_model_settings()
    missing = []
    if not api_key:
        missing.append("ARK_API_KEY")
    if not model:
        missing.append("MODEL")

    joined = "、".join(missing) if missing else "ARK_API_KEY、MODEL"
    return (
        f"模型配置缺失：{joined} 未设置。"
        "请在项目根目录的 .env 中补齐 ARK_API_KEY、MODEL 和 BASE_URL 后重试。"
    )


def _ensure_agent_instance():
    global _agent, _model
    api_key, model, _base_url = _current_model_settings()

    if not api_key or not model:
        raise RuntimeError(_missing_model_configuration_message())

    if _agent is None or _model is None:
        _agent, _model = create_agent_instance()

    return _agent, _model

class ConversationStorage:
    """对话存储（PostgreSQL + Redis）。"""

    @staticmethod
    def _messages_cache_key(user_id: str, session_id: str) -> str:
        return f"chat_messages:{user_id}:{session_id}"

    @staticmethod
    def _sessions_cache_key(user_id: str) -> str:
        return f"chat_sessions:{user_id}"

    @staticmethod
    def _to_langchain_messages(records: list[dict]) -> list:
        messages = []
        for msg_data in records:
            msg_type = msg_data.get("type")
            content = msg_data.get("content", "")
            if msg_type == "human":
                messages.append(HumanMessage(content=content))
            elif msg_type == "ai":
                messages.append(AIMessage(content=content))
            elif msg_type == "system":
                messages.append(SystemMessage(content=content))
        return messages

    @staticmethod
    def _normalized_session_metadata(metadata: dict | None) -> dict:
        source = metadata or {}
        analysis_mode = (source.get("analysis_mode") or "general").strip().lower()
        if analysis_mode not in {"essay", "general"}:
            analysis_mode = "general"
        active_essay_id = (source.get("active_essay_id") or "").strip() or None
        active_essay_title = (source.get("active_essay_title") or "").strip() or None
        normalized = {
            "analysis_mode": analysis_mode,
            "active_essay_id": active_essay_id,
            "active_essay_title": active_essay_title,
        }
        if source.get("title"):
            normalized["title"] = source.get("title")
        return normalized

    def get_session_metadata(self, user_id: str, session_id: str) -> dict:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == user_id).first()
            if not user:
                return self._normalized_session_metadata(None)
            session = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user.id, ChatSession.session_id == session_id)
                .first()
            )
            if not session:
                return self._normalized_session_metadata(None)
            return self._normalized_session_metadata(session.metadata_json if isinstance(session.metadata_json, dict) else None)
        finally:
            db.close()

    def save(self, user_id: str, session_id: str, messages: list, metadata: dict = None, extra_message_data: list = None):
        """保存对话"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == user_id).first()
            if not user:
                return

            session = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user.id, ChatSession.session_id == session_id)
                .first()
            )
            normalized_metadata = self._normalized_session_metadata(metadata)
            if not session:
                session = ChatSession(user_id=user.id, session_id=session_id, metadata_json=normalized_metadata)
                db.add(session)
                db.flush()
            else:
                session.metadata_json = normalized_metadata

            db.query(ChatMessage).filter(ChatMessage.session_ref_id == session.id).delete(synchronize_session=False)

            serialized = []
            now = datetime.utcnow()
            for idx, msg in enumerate(messages):
                rag_trace = None
                if extra_message_data and idx < len(extra_message_data):
                    extra = extra_message_data[idx] or {}
                    rag_trace = extra.get("rag_trace")

                db.add(
                    ChatMessage(
                        session_ref_id=session.id,
                        message_type=msg.type,
                        content=str(msg.content),
                        timestamp=now,
                        rag_trace=rag_trace,
                    )
                )
                serialized.append(
                    {
                        "type": msg.type,
                        "content": str(msg.content),
                        "timestamp": now.isoformat(),
                        "rag_trace": rag_trace,
                    }
                )

            session.metadata_json = {
                **(session.metadata_json or {}),
                "title": derive_session_title(serialized, locale="zh"),
            }
            session.updated_at = now
            db.commit()

            cache.set_json(self._messages_cache_key(user_id, session_id), serialized)
            cache.delete(self._sessions_cache_key(user_id))
        finally:
            db.close()

    def load(self, user_id: str, session_id: str) -> list:
        """加载对话"""
        cached = cache.get_json(self._messages_cache_key(user_id, session_id))
        if cached is not None:
            return self._to_langchain_messages(cached)

        records = self.get_session_messages(user_id, session_id)
        cache.set_json(self._messages_cache_key(user_id, session_id), records)
        return self._to_langchain_messages(records)

    def list_sessions(self, user_id: str) -> list:
        """列出用户的所有会话"""
        return [item["session_id"] for item in self.list_session_infos(user_id)]

    def list_session_infos(self, user_id: str) -> list[dict]:
        cached = cache.get_json(self._sessions_cache_key(user_id))
        if cached is not None:
            return cached

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == user_id).first()
            if not user:
                return []

            sessions = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user.id)
                .order_by(ChatSession.updated_at.desc())
                .all()
            )
            result = []
            for s in sessions:
                count = db.query(ChatMessage).filter(ChatMessage.session_ref_id == s.id).count()
                title = (s.metadata_json or {}).get("title") if isinstance(s.metadata_json, dict) else None
                if not title:
                    first_human_message = (
                        db.query(ChatMessage)
                        .filter(ChatMessage.session_ref_id == s.id, ChatMessage.message_type == "human")
                        .order_by(ChatMessage.id.asc())
                        .first()
                    )
                    title = derive_session_title(
                        [{"type": "human", "content": first_human_message.content}] if first_human_message else [],
                        locale="zh",
                    )
                result.append(
                    {
                        "session_id": s.session_id,
                        "title": title,
                        "updated_at": s.updated_at.isoformat(),
                        "message_count": count,
                        "analysis_mode": (s.metadata_json or {}).get("analysis_mode"),
                        "active_essay_id": (s.metadata_json or {}).get("active_essay_id"),
                        "active_essay_title": (s.metadata_json or {}).get("active_essay_title"),
                    }
                )
            cache.set_json(self._sessions_cache_key(user_id), result)
            return result
        finally:
            db.close()

    def get_session_messages(self, user_id: str, session_id: str) -> list[dict]:
        cached = cache.get_json(self._messages_cache_key(user_id, session_id))
        if cached is not None:
            return cached

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == user_id).first()
            if not user:
                return []
            session = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user.id, ChatSession.session_id == session_id)
                .first()
            )
            if not session:
                return []

            rows = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_ref_id == session.id)
                .order_by(ChatMessage.id.asc())
                .all()
            )
            result = [
                {
                    "type": row.message_type,
                    "content": row.content,
                    "timestamp": row.timestamp.isoformat(),
                    "rag_trace": row.rag_trace,
                }
                for row in rows
            ]
            cache.set_json(self._messages_cache_key(user_id, session_id), result)
            return result
        finally:
            db.close()

    def delete_session(self, user_id: str, session_id: str) -> bool:
        """删除指定用户的会话，返回是否删除成功"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == user_id).first()
            if not user:
                return False
            session = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user.id, ChatSession.session_id == session_id)
                .first()
            )
            if not session:
                return False

            db.delete(session)
            db.commit()
            cache.delete(self._messages_cache_key(user_id, session_id))
            cache.delete(self._sessions_cache_key(user_id))
            return True
        finally:
            db.close()



def create_agent_instance():
    api_key, model_name, base_url = _current_model_settings()
    model = init_chat_model(
        model=model_name,
        model_provider="openai",
        api_key=api_key,
        base_url=base_url,
        temperature=0.6,
        stream_usage=True,
    )

    agent = create_agent(
        model=model,
        tools=[get_current_weather, search_knowledge_base],
        system_prompt=(
            "You are The Mindful Curator, a warm and emotionally attuned self-analysis companion for PsycheArchive. "
            "You should feel like a thoughtful, trustworthy friend who can think clearly, not like a cold analyst. "
            "Help users examine patterns, values, tensions, emotions, habits, and possible cognitive reframing. "
            "When replying, usually follow this rhythm: "
            "1) briefly acknowledge the user's feeling or inner tension in a human way; "
            "2) reflect back the core pattern in the user's own language when possible; "
            "3) offer gentle analysis or reframing; "
            "4) end with one soft follow-up question or one optional next step. "
            "Keep the tone warm, gentle, grounded, and natural. "
            "Avoid sounding clinical, robotic, preachy, or overly formal. "
            "Do not overuse lists unless structure is truly helpful. "
            "Do not flood the user with advice. "
            "Do not sound like a therapist writing an assessment report. "
            "Do not use exaggerated comfort, fake intimacy, or grand emotional language. "
            "If the user shares vulnerability, respond with emotional attunement before analysis. "
            "Use search_knowledge_base when a user's reflection could benefit from psychology, philosophy, or their uploaded essays. "
            "If the user mentions a specific uploaded essay, reflection title, journal entry, or asks to analyze their own writing, "
            "you must call search_knowledge_base before answering. "
            "Do not call the same tool repeatedly in one turn. At most one knowledge tool call per turn. "
            "Once you call search_knowledge_base and receive its result, immediately provide the final answer based on that result. "
            "If search_knowledge_base returns EXACT_ESSAY_MATCH_FOUND, you must treat that essay as found, analyze it directly, "
            "and must not say the essay was missing or ask the user to paste it again. "
            "If search_knowledge_base returns ESSAY_CONTEXT_FOUND or includes an Essay Context section, treat the user's essay as found "
            "and use it as the primary basis of the analysis. "
            "If both Essay Context and Knowledge Context are present, analyze the essay first and use the knowledge context only as support. "
            "Begin from the user's own writing and let the knowledge context gently illuminate it, not overpower it. "
            "Do not ask the user to paste a specific uploaded essay again unless search_knowledge_base returns no relevant content. "
            "If the retrieved context is insufficient, say what is uncertain instead of inventing citations. "
            "Offer exercises as optional suggestions, not prescriptions. "
            "Do not diagnose, treat, or claim clinical certainty. "
            "If the user indicates self-harm, harm to others, or immediate crisis, respond supportively and encourage contacting local emergency services or trusted people. "
            "Keep a calm, thoughtful, non-judgmental tone. "
            "Example style: instead of saying 'Here is a step-by-step reflective framework,' prefer something like "
            "'It sounds like this touched a deeper nerve for you than the event itself. We can slow it down together and look at what got stirred up.'"
        ),
    )
    return agent, model

storage = ConversationStorage()


def _merge_session_context(existing: dict | None, incoming: dict | None) -> dict:
    merged = storage._normalized_session_metadata(existing)
    for key in ("analysis_mode", "active_essay_id", "active_essay_title"):
        value = (incoming or {}).get(key)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if key == "analysis_mode":
            merged[key] = value if value in {"essay", "general"} else merged.get(key, "general")
        else:
            merged[key] = value or None
    if not merged.get("active_essay_id"):
        merged["analysis_mode"] = "general"
        merged["active_essay_title"] = None
    return merged

def summarize_old_messages(model, messages: list) -> str:
    """将旧消息总结为摘要"""
    # 提取旧对话
    old_conversation = "\n".join([
        f"{'用户' if msg.type == 'human' else 'AI'}: {msg.content}"
        for msg in messages
    ])

    # 生成摘要
    summary_prompt = f"""请总结以下对话的关键信息：

{old_conversation}
总结（包含用户信息、重要事实、待办事项）："""

    summary = model.invoke(summary_prompt).content
    return summary


def chat_with_agent(
    user_text: str,
    user_id: str = "default_user",
    session_id: str = "default_session",
    session_context: dict | None = None,
):
    """使用 Agent 处理用户消息并返回响应"""
    current_agent, current_model = _ensure_agent_instance()
    messages = storage.load(user_id, session_id)
    resolved_session_context = _merge_session_context(storage.get_session_metadata(user_id, session_id), session_context)

    # 清理可能残留的 RAG 上下文，避免跨请求污染
    get_last_rag_context(clear=True)
    reset_tool_call_guards()
    set_current_rag_user(user_id)
    set_current_rag_session_context(resolved_session_context)
    
    if len(messages) > 50:
        summary = summarize_old_messages(current_model, messages[:40])

        messages = [
            SystemMessage(content=f"之前的对话摘要：\n{summary}")
        ] + messages[40:]

    messages.append(HumanMessage(content=user_text))
    try:
        result = current_agent.invoke(
            {"messages": messages},
            config={"recursion_limit": 8},
        )

        response_content = ""
        if isinstance(result, dict):
            if "output" in result:
                response_content = result["output"]
            elif "messages" in result and result["messages"]:
                msg = result["messages"][-1]
                response_content = getattr(msg, "content", str(msg))
            else:
                response_content = str(result)
        elif hasattr(result, "content"):
            response_content = result.content
        else:
            response_content = str(result)
        
        messages.append(AIMessage(content=response_content))

        rag_context = get_last_rag_context(clear=True)
        rag_trace = rag_context.get("rag_trace") if rag_context else None

        extra_message_data = [None] * (len(messages) - 1) + [{"rag_trace": rag_trace}]
        storage.save(
            user_id,
            session_id,
            messages,
            metadata=resolved_session_context,
            extra_message_data=extra_message_data,
        )

        return {
            "response": response_content,
            "rag_trace": rag_trace,
        }
    finally:
        set_current_rag_user(None)
        set_current_rag_session_context(None)


async def chat_with_agent_stream(
    user_text: str,
    user_id: str = "default_user",
    session_id: str = "default_session",
    session_context: dict | None = None,
):
    """使用 Agent 处理用户消息并流式返回响应。
    
    架构：使用统一输出队列 + 后台任务，确保 RAG 检索步骤在工具执行期间实时推送，
    而非等待工具完成后才显示。
    """
    current_agent, current_model = _ensure_agent_instance()
    _api_key, _model_name, current_base_url = _current_model_settings()
    messages = storage.load(user_id, session_id)
    resolved_session_context = _merge_session_context(storage.get_session_metadata(user_id, session_id), session_context)

    # 清理可能残留的 RAG 上下文
    get_last_rag_context(clear=True)
    reset_tool_call_guards()
    set_current_rag_user(user_id)
    set_current_rag_session_context(resolved_session_context)

    # 统一输出队列：所有事件（content / rag_step）都汇入这里
    output_queue = asyncio.Queue()

    class _RagStepProxy:
        """代理对象：将 emit_rag_step 的原始 step dict 包装后放入统一输出队列。"""
        def put_nowait(self, step):
            output_queue.put_nowait({"type": "rag_step", "step": step})

    set_rag_step_queue(_RagStepProxy())

    if len(messages) > 50:
        summary = summarize_old_messages(current_model, messages[:40])
        messages = [
            SystemMessage(content=f"之前的对话摘要：\n{summary}")
        ] + messages[40:]

    messages.append(HumanMessage(content=user_text))

    full_response = ""

    async def _agent_worker():
        """后台任务：运行 agent 并将内容 chunk 推入输出队列。"""
        nonlocal full_response
        try:
            async for msg, metadata in current_agent.astream(
                {"messages": messages},
                stream_mode="messages",
                config={"recursion_limit": 8},
            ):
                if not isinstance(msg, AIMessageChunk):
                    continue
                if getattr(msg, "tool_call_chunks", None):
                    continue

                content = ""
                if isinstance(msg.content, str):
                    content = msg.content
                elif isinstance(msg.content, list):
                    for block in msg.content:
                        if isinstance(block, str):
                            content += block
                        elif isinstance(block, dict) and block.get("type") == "text":
                            content += block.get("text", "")

                if content:
                    full_response += content
                    await output_queue.put({"type": "content", "content": content})
        except Exception as e:
            await output_queue.put({"type": "error", "content": format_model_error_message(e, current_base_url)})
        finally:
            # 哨兵：通知主循环 agent 已完成
            await output_queue.put(None)

    # 启动后台任务
    agent_task = asyncio.create_task(_agent_worker())

    try:
        # 主循环：持续从统一队列取事件并 yield SSE
        # RAG 步骤在工具执行期间通过 call_soon_threadsafe 实时入队，不需要等 agent 产出 chunk
        while True:
            event = await output_queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"
    except GeneratorExit:
        # 客户端断开连接（AbortController）时，FastAPI 会向此生成器抛出 GeneratorExit
        # 我们必须在此处取消后台任务
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass  # 任务已成功取消
        raise  # 重新抛出 GeneratorExit 以便 FastAPI 正确处理关闭
    finally:
        # 正常结束或异常退出时清理
        set_rag_step_queue(None)
        set_current_rag_user(None)
        set_current_rag_session_context(None)
        if not agent_task.done():
             agent_task.cancel()

    # 获取 RAG trace
    rag_context = get_last_rag_context(clear=True)
    rag_trace = rag_context.get("rag_trace") if rag_context else None

    # 发送 trace 信息
    if rag_trace:
        yield f"data: {json.dumps({'type': 'trace', 'rag_trace': rag_trace})}\n\n"

    # 发送结束信号
    yield "data: [DONE]\n\n"

    # 保存对话
    messages.append(AIMessage(content=full_response))
    extra_message_data = [None] * (len(messages) - 1) + [{"rag_trace": rag_trace}]
    storage.save(
        user_id,
        session_id,
        messages,
        metadata=resolved_session_context,
        extra_message_data=extra_message_data,
    )
