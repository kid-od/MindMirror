"""FastAPI 请求/响应模型。

这些 Pydantic schema 是前后端契约：routes/* 返回这些结构，frontend/script.js
按相同字段渲染会话、引用、上传进度、洞察和时间线。
"""

from pydantic import BaseModel
from typing import Any, Optional, List


# 认证与当前用户
class RegisterRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"
    admin_code: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class CurrentUserResponse(BaseModel):
    username: str
    role: str


# 对话与 RAG trace
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"
    active_essay_id: Optional[str] = None
    active_essay_title: Optional[str] = None
    analysis_mode: Optional[str] = "general"


class RetrievedChunk(BaseModel):
    filename: str
    page_number: Optional[str | int] = None
    text: Optional[str] = None
    score: Optional[float] = None
    rrf_rank: Optional[int] = None
    rerank_score: Optional[float] = None


class RagTrace(BaseModel):
    tool_used: bool
    tool_name: str
    query: Optional[str] = None
    expanded_query: Optional[str] = None
    step_back_question: Optional[str] = None
    step_back_answer: Optional[str] = None
    expansion_type: Optional[str] = None
    hypothetical_doc: Optional[str] = None
    retrieval_stage: Optional[str] = None
    grade_score: Optional[str] = None
    grade_route: Optional[str] = None
    rewrite_needed: Optional[bool] = None
    rewrite_strategy: Optional[str] = None
    rewrite_query: Optional[str] = None
    rerank_enabled: Optional[bool] = None
    rerank_applied: Optional[bool] = None
    rerank_model: Optional[str] = None
    rerank_endpoint: Optional[str] = None
    rerank_error: Optional[str] = None
    retrieval_mode: Optional[str] = None
    candidate_k: Optional[int] = None
    leaf_retrieve_level: Optional[int] = None
    auto_merge_enabled: Optional[bool] = None
    auto_merge_applied: Optional[bool] = None
    auto_merge_threshold: Optional[int] = None
    auto_merge_replaced_chunks: Optional[int] = None
    auto_merge_steps: Optional[int] = None
    essay_context: Optional[dict[str, Any]] = None
    knowledge_context: Optional[dict[str, Any]] = None
    retrieved_chunks: Optional[List[RetrievedChunk]] = None
    initial_retrieved_chunks: Optional[List[RetrievedChunk]] = None
    expanded_retrieved_chunks: Optional[List[RetrievedChunk]] = None


class ChatResponse(BaseModel):
    response: str
    rag_trace: Optional[RagTrace] = None


# 会话列表与历史消息
class MessageInfo(BaseModel):
    type: str
    content: str
    timestamp: str
    rag_trace: Optional[RagTrace] = None


class SessionMessagesResponse(BaseModel):
    messages: List[MessageInfo]
    analysis_mode: Optional[str] = None
    active_essay_id: Optional[str] = None
    active_essay_title: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    title: str
    updated_at: str
    message_count: int
    analysis_mode: Optional[str] = None
    active_essay_id: Optional[str] = None
    active_essay_title: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]


class SessionDeleteResponse(BaseModel):
    session_id: str
    message: str


class DailyQuoteResponse(BaseModel):
    text: str
    author: str
    language: str
    source: str
    fallback: bool


# 公共知识库文档
class DocumentInfo(BaseModel):
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: Optional[str] = None
    cover_url: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]


class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_processed: int
    message: str


class DocumentDeleteResponse(BaseModel):
    filename: str
    chunks_deleted: int
    message: str


# 私密随笔
class EssayInfo(BaseModel):
    essay_id: Optional[str] = None
    title: Optional[str] = None
    filename: str
    file_type: str
    language: Optional[str] = None
    chunk_count: int
    uploaded_at: Optional[str] = None


class EssayListResponse(BaseModel):
    essays: List[EssayInfo]


class EssayDeleteResponse(BaseModel):
    filename: str
    chunks_deleted: int
    message: str


# 洞察与时间线聚合视图
class InsightTotals(BaseModel):
    essays: int
    sessions: int
    documents: int


class InsightTheme(BaseModel):
    label: str
    count: int


class ActivityPoint(BaseModel):
    date: str
    essays: int
    sessions: int
    documents: int


class InsightsResponse(BaseModel):
    totals: InsightTotals
    top_themes: List[InsightTheme]
    activity: List[ActivityPoint]
    recent_essays: List[EssayInfo]
    recent_sessions: List[SessionInfo]


class TimelineEvent(BaseModel):
    kind: str
    timestamp: str
    title: str
    subtitle: str
    reference: Optional[str] = None


class TimelineGroup(BaseModel):
    date: str
    items: List[TimelineEvent]


class TimelineResponse(BaseModel):
    groups: List[TimelineGroup]
