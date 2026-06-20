from typing import Optional
from dotenv import load_dotenv
try:
    from langchain_core.tools import tool
except ImportError:
    from langchain_core.tools import tool

load_dotenv()

_LAST_RAG_CONTEXT = None
_KNOWLEDGE_TOOL_CALLS_THIS_TURN = 0
_RAG_STEP_QUEUE = None  # asyncio.Queue, set by agent before streaming
_RAG_STEP_LOOP = None   # asyncio loop, captured when setting queue
_CURRENT_RAG_USER_ID = None
_CURRENT_RAG_SESSION_CONTEXT = None


def _set_last_rag_context(context: dict):
    global _LAST_RAG_CONTEXT
    _LAST_RAG_CONTEXT = context


def get_last_rag_context(clear: bool = True) -> Optional[dict]:
    """获取最近一次 RAG 检索上下文，默认读取后清空。"""
    global _LAST_RAG_CONTEXT
    context = _LAST_RAG_CONTEXT
    if clear:
        _LAST_RAG_CONTEXT = None
    return context


def reset_tool_call_guards():
    """每轮对话开始时重置工具调用计数。"""
    global _KNOWLEDGE_TOOL_CALLS_THIS_TURN
    _KNOWLEDGE_TOOL_CALLS_THIS_TURN = 0


def set_current_rag_user(user_id: str | None):
    global _CURRENT_RAG_USER_ID
    _CURRENT_RAG_USER_ID = user_id


def get_current_rag_user() -> Optional[str]:
    return _CURRENT_RAG_USER_ID


def set_current_rag_session_context(context: dict | None):
    global _CURRENT_RAG_SESSION_CONTEXT
    _CURRENT_RAG_SESSION_CONTEXT = dict(context or {}) if context else None


def get_current_rag_session_context() -> Optional[dict]:
    return dict(_CURRENT_RAG_SESSION_CONTEXT or {}) if _CURRENT_RAG_SESSION_CONTEXT else None


def set_rag_step_queue(queue):
    """设置 RAG 步骤队列，并捕获当前事件循环以便跨线程调度。"""
    global _RAG_STEP_QUEUE, _RAG_STEP_LOOP
    _RAG_STEP_QUEUE = queue
    if queue:
        import asyncio
        try:
            _RAG_STEP_LOOP = asyncio.get_running_loop()
        except RuntimeError:
            _RAG_STEP_LOOP = asyncio.get_event_loop()
    else:
        _RAG_STEP_LOOP = None


def emit_rag_step(icon: str, label: str, detail: str = ""):
    """向队列发送一个 RAG 检索步骤。支持跨线程安全调用。"""
    global _RAG_STEP_QUEUE, _RAG_STEP_LOOP
    if _RAG_STEP_QUEUE is not None and _RAG_STEP_LOOP is not None:
        step = {"icon": icon, "label": label, "detail": detail}
        try:
            if not _RAG_STEP_LOOP.is_closed():
                _RAG_STEP_LOOP.call_soon_threadsafe(_RAG_STEP_QUEUE.put_nowait, step)
        except Exception:
            pass


def _format_search_results(docs: list[dict], rag_trace: dict) -> str:
    essay_docs = [result for result in docs if result.get("document_domain") == "essay"]
    knowledge_docs = [result for result in docs if result.get("document_domain") != "essay"]

    def _render_block(items: list[dict]) -> str:
        formatted = []
        for i, result in enumerate(items, 1):
            source = result.get("filename", "Unknown")
            page = result.get("page_number", "N/A")
            text = result.get("text", "")
            formatted.append(f"[{i}] {source} (Page {page}):\n{text}")
        return "\n\n---\n\n".join(formatted)

    essay_context = (rag_trace or {}).get("essay_context") or {}
    knowledge_context = (rag_trace or {}).get("knowledge_context") or {}
    retrieval_mode = (rag_trace or {}).get("retrieval_mode")
    if not essay_context and retrieval_mode == "exact_title_match" and essay_docs:
        essay_context = {"found": True, "retrieval_mode": "exact_title_match"}
    if not knowledge_context and knowledge_docs:
        knowledge_context = {"found": True}
    sections = []

    if essay_context.get("found") and essay_docs:
        matched = ", ".join(sorted({doc.get("filename", "Unknown") for doc in essay_docs}))
        sections.extend(
            [
                f"EXACT_ESSAY_MATCH_FOUND: {matched}" if essay_context.get("retrieval_mode") == "exact_title_match" else f"ESSAY_CONTEXT_FOUND: {matched}",
                "These excerpts are from the user's uploaded essay. Do not say the essay was not found.",
                "Analyze the user's essay first, then use any auxiliary knowledge as supporting context.",
                "",
                "Essay Context:",
                _render_block(essay_docs),
            ]
        )

    if knowledge_context.get("found") and knowledge_docs:
        if sections:
            sections.append("")
        sections.extend(
            [
                "Knowledge Context:",
                _render_block(knowledge_docs),
            ]
        )

    if sections:
        return "\n".join(sections)

    return "Retrieved Chunks:\n" + _render_block(docs)


@tool("search_knowledge_base")
def search_knowledge_base(query: str) -> str:
    """Search for information in the knowledge base using hybrid retrieval (dense + sparse vectors)."""
    # ... guards omitted ...
    global _KNOWLEDGE_TOOL_CALLS_THIS_TURN
    if _KNOWLEDGE_TOOL_CALLS_THIS_TURN >= 1:
        return (
            "TOOL_CALL_LIMIT_REACHED: search_knowledge_base has already been called once in this turn. "
            "Use the existing retrieval result and provide the final answer directly."
        )
    _KNOWLEDGE_TOOL_CALLS_THIS_TURN += 1

    from rag_pipeline import run_rag_graph

    # 在同步工具中获取当前的 Loop 可能不可靠，但我们之前是通过 call_soon_threadsafe 调度的。
    # 这里 _RAG_STEP_QUEUE 是在主线程/Loop 设置的全局变量。
    # 如果工具运行在线程池中，它是可以访问到全局变量 _RAG_STEP_QUEUE 的。
    # emit_rag_step 内部做了 try-except 和 get_event_loop()。

    # 问题可能出在 asyncio.get_event_loop() 在子线程中调用会报错或者拿不到主线程的loop。
    # 我们应该在 set_rag_step_queue 时也保存 loop 引用，或者在 emit_rag_step 中更健壮地获取 loop。

    try:
        rag_result = run_rag_graph(
            query,
            user_id=get_current_rag_user(),
            session_context=get_current_rag_session_context(),
        )
    except TypeError:
        rag_result = run_rag_graph(query, user_id=get_current_rag_user())

    docs = rag_result.get("docs", []) if isinstance(rag_result, dict) else []
    rag_trace = rag_result.get("rag_trace", {}) if isinstance(rag_result, dict) else {}
    if rag_trace:
        _set_last_rag_context({"rag_trace": rag_trace})

    if not docs:
        return "No relevant documents found in the knowledge base."

    return _format_search_results(docs, rag_trace)
