"""RAG 检索工具函数。

这里封装检索层的全部细节：Milvus collection 选择、公共/私密作用域过滤、
精确随笔标题匹配、auto-merging、rerank 适配和 query expansion 辅助模型。
"""

from collections import defaultdict
from typing import List, Tuple, Dict, Any
import os
import json
import re
import requests
from pathlib import Path
from dotenv import load_dotenv

from milvus_client import MilvusManager
from embedding import embedding_service as _embedding_service
from parent_chunk_store import ParentChunkStore
try:
    from essay_store import EssayStore
except Exception:
    try:
        from backend.essay_store import EssayStore
    except Exception:
        class EssayStore:  # type: ignore[no-redef]
            def find_by_id(self, owner_id, essay_id):
                return None

            def find_by_titles(self, owner_id, titles):
                return None

            def find_by_filename(self, owner_id, filename):
                return None
from langchain.chat_models import init_chat_model
from config import normalize_base_url

load_dotenv()

ARK_API_KEY = os.getenv("ARK_API_KEY")
MODEL = os.getenv("MODEL")
BASE_URL = normalize_base_url(os.getenv("BASE_URL"))
RERANK_MODEL = os.getenv("RERANK_MODEL")
RERANK_BINDING_HOST = os.getenv("RERANK_BINDING_HOST")
RERANK_API_KEY = os.getenv("RERANK_API_KEY")
AUTO_MERGE_ENABLED = os.getenv("AUTO_MERGE_ENABLED", "true").lower() != "false"
AUTO_MERGE_THRESHOLD = int(os.getenv("AUTO_MERGE_THRESHOLD", "2"))
LEAF_RETRIEVE_LEVEL = int(os.getenv("LEAF_RETRIEVE_LEVEL", "3"))
KNOWLEDGE_COLLECTION = os.getenv("MILVUS_KNOWLEDGE_COLLECTION") or os.getenv("MILVUS_COLLECTION", "embeddings_collection")
ESSAY_COLLECTION = os.getenv("MILVUS_ESSAY_COLLECTION", "essay_chunks")


def _create_milvus_manager(collection_name: str):
    try:
        return MilvusManager(collection_name=collection_name)
    except TypeError:
        return MilvusManager()

# 全局初始化检索依赖（与 api 共用 embedding_service，保证 BM25 状态一致）
_knowledge_milvus_manager = _create_milvus_manager(KNOWLEDGE_COLLECTION)
_essay_milvus_manager = _create_milvus_manager(ESSAY_COLLECTION)
_legacy_milvus_manager = None if ESSAY_COLLECTION == KNOWLEDGE_COLLECTION else _create_milvus_manager(KNOWLEDGE_COLLECTION)
_milvus_manager = _knowledge_milvus_manager
_parent_chunk_store = ParentChunkStore()
_essay_store = EssayStore()

_stepback_model = None
_RETRIEVE_OUTPUT_FIELDS = [
    "text",
    "filename",
    "file_type",
    "page_number",
    "chunk_id",
    "parent_chunk_id",
    "root_chunk_id",
    "chunk_level",
    "chunk_idx",
    "visibility",
    "owner_id",
    "document_domain",
]


def _is_qwen_rerank_model() -> bool:
    model = (RERANK_MODEL or "").strip().lower()
    return model.startswith("qwen3-rerank") or model.startswith("qwen3-vl-rerank")


def _get_rerank_api_key() -> str:
    return (RERANK_API_KEY or ARK_API_KEY or "").strip()


def _get_rerank_endpoint() -> str:
    host = (RERANK_BINDING_HOST or "").strip().rstrip("/")
    if not host:
        return "https://dashscope.aliyuncs.com/compatible-api/v1/reranks" if _is_qwen_rerank_model() else ""

    if "dashscope.aliyuncs.com" in host:
        if host.endswith("/compatible-api/v1/reranks"):
            return host
        if host.endswith("/compatible-api/v1"):
            return f"{host}/reranks"
        if host.endswith("/api/v1/services/rerank/text-rerank/text-rerank"):
            return host
        return "https://dashscope.aliyuncs.com/compatible-api/v1/reranks"

    return host if host.endswith("/v1/rerank") else f"{host}/v1/rerank"


def _extract_rerank_results(payload: Dict[str, Any]) -> List[dict]:
    output = payload.get("output")
    if isinstance(output, dict):
        results = output.get("results")
        if isinstance(results, list):
            return results

    results = payload.get("results")
    return results if isinstance(results, list) else []


def _escape_filter_value(value: str) -> str:
    return (value or "").replace("\\", "\\\\").replace('"', '\\"')


def build_scope_filter(user_id: str | None) -> str:
    """构造“公共知识库 OR 当前用户私密随笔”的混合检索过滤条件。"""
    safe_user = _escape_filter_value(user_id or "")
    public_filter = '(visibility == "public" and document_domain == "knowledge_base")'
    private_filter = (
        f'(visibility == "private" and owner_id == "{safe_user}" and '
        'document_domain == "essay")'
    )
    return f"{public_filter} or {private_filter}"


def build_knowledge_filter() -> str:
    """只检索公共知识库，供公共知识通道使用。"""
    return '(visibility == "public" and document_domain == "knowledge_base")'


def build_essay_filter(user_id: str | None) -> str:
    """只检索当前用户私密随笔，避免跨账号泄漏。"""
    safe_user = _escape_filter_value(user_id or "")
    return (
        f'visibility == "private" and owner_id == "{safe_user}" and document_domain == "essay"'
    )


def _normalize_title_key(value: str) -> str:
    stem = Path((value or "").strip()).stem
    return re.sub(r"[\s_\-]+", "", stem).casefold()


def _extract_requested_titles(query: str) -> List[str]:
    """从《标题》、“标题”等写法里提取用户点名要分析的随笔标题。"""
    text = (query or "").strip()
    if not text:
        return []

    titles: List[str] = []
    patterns = [
        r"《([^》]+)》",
        r"“([^”]+)”",
        r'"([^"]+)"',
        r"'([^']+)'",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text):
            cleaned = (match or "").strip()
            if cleaned:
                titles.append(cleaned)

    deduped: List[str] = []
    seen = set()
    for title in titles:
        normalized = _normalize_title_key(title)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(title)
    return deduped


def _private_leaf_filter(user_id: str) -> str:
    safe_user = _escape_filter_value(user_id or "")
    return (
        f'chunk_level == {LEAF_RETRIEVE_LEVEL} and '
        f'visibility == "private" and owner_id == "{safe_user}" and document_domain == "essay"'
    )


def _legacy_private_leaf_filter(user_id: str) -> str:
    safe_user = _escape_filter_value(user_id or "")
    return (
        f'chunk_level == {LEAF_RETRIEVE_LEVEL} and '
        f'visibility == "private" and owner_id == "{safe_user}" and document_domain == "essay"'
    )


def _retrieve_requested_essay_chunks_legacy(query: str, user_id: str | None, top_k: int) -> List[dict]:
    if not user_id:
        return []

    requested_titles = _extract_requested_titles(query)
    if not requested_titles:
        return []

    title_keys = {_normalize_title_key(title) for title in requested_titles}
    scope_filter = _legacy_private_leaf_filter(user_id)
    manager = _legacy_milvus_manager or _essay_milvus_manager
    filename_rows = manager.query_all(filter_expr=scope_filter, output_fields=["filename"])

    matched_filenames: List[str] = []
    seen_filenames = set()
    for row in filename_rows:
        filename = row.get("filename", "")
        if not filename:
            continue
        if _normalize_title_key(filename) not in title_keys or filename in seen_filenames:
            continue
        seen_filenames.add(filename)
        matched_filenames.append(filename)

    matched_docs: List[dict] = []
    for filename in matched_filenames:
        file_filter = f'{scope_filter} and filename == "{_escape_filter_value(filename)}"'
        rows = manager.query_all(filter_expr=file_filter, output_fields=_RETRIEVE_OUTPUT_FIELDS)
        rows.sort(key=lambda item: (int(item.get("page_number") or 0), int(item.get("chunk_idx") or 0)))
        for row in rows:
            doc = dict(row)
            doc["score"] = float(doc.get("score") or 1.0)
            doc["exact_title_match"] = True
            matched_docs.append(doc)
            if len(matched_docs) >= top_k:
                return matched_docs
    return matched_docs


def _essay_docs_from_content(essay: dict, top_k: int) -> List[dict]:
    content = (essay.get("content") or "").strip()
    if not content:
        return []

    segments: List[str] = []
    if len(content) <= 2800:
        segments = [content]
    else:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", content) if (part or "").strip()]
        current = ""
        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= 1600:
                current = candidate
                continue
            if current:
                segments.append(current)
            current = paragraph
        if current:
            segments.append(current)
        if not segments:
            segments = [content[:1600], content[1600:3200], content[3200:4800]]
            segments = [item for item in segments if item]

    docs = []
    filename = essay.get("filename", "")
    for idx, text in enumerate(segments[: max(1, top_k)]):
        docs.append(
            {
                "filename": filename,
                "text": text,
                "file_type": essay.get("file_type", ""),
                "page_number": 0,
                "chunk_id": f'{essay.get("essay_id", filename)}::context::{idx}',
                "parent_chunk_id": "",
                "root_chunk_id": essay.get("essay_id", filename),
                "chunk_level": 1,
                "chunk_idx": idx,
                "visibility": "private",
                "owner_id": essay.get("owner_id", ""),
                "document_domain": "essay",
                "score": 1.0,
            }
        )
    return docs


def _empty_essay_context() -> dict:
    return {
        "found": False,
        "essay_id": None,
        "title": None,
        "filename": None,
        "retrieval_mode": None,
        "source": None,
    }


def _empty_knowledge_context() -> dict:
    return {
        "found": False,
        "query": None,
        "retrieval_mode": None,
        "candidate_k": 0,
        "retrieved_count": 0,
    }


def _dedupe_docs(docs: List[dict], limit: int) -> List[dict]:
    deduped = []
    seen = set()
    for item in docs:
        key = item.get("chunk_id") or (item.get("filename"), item.get("page_number"), item.get("text"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def _merge_to_parent_level(docs: List[dict], threshold: int = 2) -> Tuple[List[dict], int]:
    groups: Dict[str, List[dict]] = defaultdict(list)
    for doc in docs:
        parent_id = (doc.get("parent_chunk_id") or "").strip()
        if parent_id:
            groups[parent_id].append(doc)

    merge_parent_ids = [parent_id for parent_id, children in groups.items() if len(children) >= threshold]
    if not merge_parent_ids:
        return docs, 0

    parent_docs = _parent_chunk_store.get_documents_by_ids(merge_parent_ids)
    parent_map = {item.get("chunk_id", ""): item for item in parent_docs if item.get("chunk_id")}

    merged_docs: List[dict] = []
    merged_count = 0
    for doc in docs:
        parent_id = (doc.get("parent_chunk_id") or "").strip()
        if not parent_id or parent_id not in parent_map:
            merged_docs.append(doc)
            continue
        parent_doc = dict(parent_map[parent_id])
        if any(
            (parent_doc.get(field) or "") != (doc.get(field) or "")
            for field in ("visibility", "owner_id", "document_domain", "filename")
        ):
            merged_docs.append(doc)
            continue
        score = doc.get("score")
        if score is not None:
            parent_doc["score"] = max(float(parent_doc.get("score", score)), float(score))
        parent_doc["merged_from_children"] = True
        parent_doc["merged_child_count"] = len(groups[parent_id])
        merged_docs.append(parent_doc)
        merged_count += 1

    deduped: List[dict] = []
    seen = set()
    for item in merged_docs:
        key = item.get("chunk_id") or (item.get("filename"), item.get("page_number"), item.get("text"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped, merged_count


def _auto_merge_documents(docs: List[dict], top_k: int) -> Tuple[List[dict], Dict[str, Any]]:
    if not AUTO_MERGE_ENABLED or not docs:
        return docs[:top_k], {
            "auto_merge_enabled": AUTO_MERGE_ENABLED,
            "auto_merge_applied": False,
            "auto_merge_threshold": AUTO_MERGE_THRESHOLD,
            "auto_merge_replaced_chunks": 0,
            "auto_merge_steps": 0,
        }

    # 两段自动合并：L3->L2，再 L2->L1。
    merged_docs, merged_count_l3_l2 = _merge_to_parent_level(docs, threshold=AUTO_MERGE_THRESHOLD)
    merged_docs, merged_count_l2_l1 = _merge_to_parent_level(merged_docs, threshold=AUTO_MERGE_THRESHOLD)

    merged_docs.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    merged_docs = merged_docs[:top_k]

    replaced_count = merged_count_l3_l2 + merged_count_l2_l1
    return merged_docs, {
        "auto_merge_enabled": AUTO_MERGE_ENABLED,
        "auto_merge_applied": replaced_count > 0,
        "auto_merge_threshold": AUTO_MERGE_THRESHOLD,
        "auto_merge_replaced_chunks": replaced_count,
        "auto_merge_steps": int(merged_count_l3_l2 > 0) + int(merged_count_l2_l1 > 0),
    }


def _retrieve_knowledge_chunks(
    query: str,
    top_k: int,
    user_id: str | None = None,
    include_private_essays: bool = False,
) -> Dict[str, Any]:
    candidate_k = max(top_k * 3, top_k)
    scope_filter = build_scope_filter(user_id) if include_private_essays else build_knowledge_filter()
    filter_expr = f"chunk_level == {LEAF_RETRIEVE_LEVEL} and ({scope_filter})"
    try:
        dense_embeddings = _embedding_service.get_embeddings([query])
        dense_embedding = dense_embeddings[0]
        sparse_embedding = _embedding_service.get_sparse_embedding(query)

        retrieved = _knowledge_milvus_manager.hybrid_retrieve(
            dense_embedding=dense_embedding,
            sparse_embedding=sparse_embedding,
            top_k=candidate_k,
            filter_expr=filter_expr,
        )
        reranked, rerank_meta = _rerank_documents(query=query, docs=retrieved, top_k=top_k)
        merged_docs, merge_meta = _auto_merge_documents(docs=reranked, top_k=top_k)
        rerank_meta["retrieval_mode"] = "hybrid"
        rerank_meta["candidate_k"] = candidate_k
        rerank_meta["leaf_retrieve_level"] = LEAF_RETRIEVE_LEVEL
        rerank_meta.update(merge_meta)
        return {"docs": merged_docs, "meta": rerank_meta}
    except Exception:
        try:
            dense_embeddings = _embedding_service.get_embeddings([query])
            dense_embedding = dense_embeddings[0]
            retrieved = _knowledge_milvus_manager.dense_retrieve(
                dense_embedding=dense_embedding,
                top_k=candidate_k,
                filter_expr=filter_expr,
            )
            reranked, rerank_meta = _rerank_documents(query=query, docs=retrieved, top_k=top_k)
            merged_docs, merge_meta = _auto_merge_documents(docs=reranked, top_k=top_k)
            rerank_meta["retrieval_mode"] = "dense_fallback"
            rerank_meta["candidate_k"] = candidate_k
            rerank_meta["leaf_retrieve_level"] = LEAF_RETRIEVE_LEVEL
            rerank_meta.update(merge_meta)
            return {"docs": merged_docs, "meta": rerank_meta}
        except Exception:
            rerank_endpoint = _get_rerank_endpoint()
            return {
                "docs": [],
                "meta": {
                    "rerank_enabled": bool(RERANK_MODEL and _get_rerank_api_key() and rerank_endpoint),
                    "rerank_applied": False,
                    "rerank_model": RERANK_MODEL,
                    "rerank_endpoint": rerank_endpoint,
                    "rerank_error": "retrieve_failed",
                    "retrieval_mode": "failed",
                    "candidate_k": candidate_k,
                    "leaf_retrieve_level": LEAF_RETRIEVE_LEVEL,
                    "auto_merge_enabled": AUTO_MERGE_ENABLED,
                    "auto_merge_applied": False,
                    "auto_merge_threshold": AUTO_MERGE_THRESHOLD,
                    "auto_merge_replaced_chunks": 0,
                    "auto_merge_steps": 0,
                    "candidate_count": 0,
                },
            }


def _build_essay_semantic_filter(user_id: str) -> str:
    return build_essay_filter(user_id)


def _retrieve_essay_semantic_chunks(query: str, user_id: str | None, top_k: int) -> List[dict]:
    if not user_id:
        return []
    filter_expr = _build_essay_semantic_filter(user_id)
    try:
        dense_embeddings = _embedding_service.get_embeddings([query])
        dense_embedding = dense_embeddings[0]
        return _essay_milvus_manager.dense_retrieve(
            dense_embedding=dense_embedding,
            top_k=top_k,
            filter_expr=filter_expr,
        )
    except Exception:
        if not _legacy_milvus_manager:
            return []
        try:
            dense_embeddings = _embedding_service.get_embeddings([query])
            dense_embedding = dense_embeddings[0]
            return _legacy_milvus_manager.dense_retrieve(
                dense_embedding=dense_embedding,
                top_k=top_k,
                filter_expr=_legacy_private_leaf_filter(user_id),
            )
        except Exception:
            return []


def _select_essay_from_context(
    query: str,
    user_id: str | None,
    top_k: int,
    title_hint_query: str | None = None,
    session_context: dict | None = None,
) -> Tuple[List[dict], dict]:
    if not user_id:
        return [], _empty_essay_context()

    session_context = session_context or {}
    analysis_mode = (session_context.get("analysis_mode") or "").strip().lower()
    active_essay_id = (session_context.get("active_essay_id") or "").strip()
    active_essay_title = (session_context.get("active_essay_title") or "").strip()

    if active_essay_id:
        essay = _essay_store.find_by_id(user_id, active_essay_id)
        if essay:
            return _essay_docs_from_content(essay, top_k=top_k), {
                "found": True,
                "essay_id": essay.get("essay_id"),
                "title": essay.get("title"),
                "filename": essay.get("filename"),
                "retrieval_mode": "session_bound",
                "source": "essay_documents",
            }

    if analysis_mode == "essay" and active_essay_title:
        essay = _essay_store.find_by_titles(user_id, [active_essay_title])
        if essay:
            return _essay_docs_from_content(essay, top_k=top_k), {
                "found": True,
                "essay_id": essay.get("essay_id"),
                "title": essay.get("title"),
                "filename": essay.get("filename"),
                "retrieval_mode": "session_bound",
                "source": "essay_documents",
            }
        legacy_docs = _retrieve_requested_essay_chunks_legacy(f"《{active_essay_title}》", user_id, top_k)
        if legacy_docs:
            filename = legacy_docs[0].get("filename")
            return legacy_docs, {
                "found": True,
                "essay_id": None,
                "title": active_essay_title,
                "filename": filename,
                "retrieval_mode": "session_bound",
                "source": "legacy_chunks",
            }

    requested_titles = _extract_requested_titles(title_hint_query or query)
    if requested_titles:
        essay = _essay_store.find_by_titles(user_id, requested_titles)
        if essay:
            return _essay_docs_from_content(essay, top_k=top_k), {
                "found": True,
                "essay_id": essay.get("essay_id"),
                "title": essay.get("title"),
                "filename": essay.get("filename"),
                "retrieval_mode": "exact_title_match",
                "source": "essay_documents",
            }

        legacy_docs = _retrieve_requested_essay_chunks_legacy(title_hint_query or query, user_id, top_k)
        if legacy_docs:
            filename = legacy_docs[0].get("filename")
            legacy_essay = _essay_store.find_by_filename(user_id, filename) if filename else None
            return legacy_docs, {
                "found": True,
                "essay_id": legacy_essay.get("essay_id") if legacy_essay else None,
                "title": legacy_essay.get("title") if legacy_essay else Path(filename or "").stem,
                "filename": filename,
                "retrieval_mode": "exact_title_match",
                "source": "legacy_chunks",
            }

    if analysis_mode == "essay":
        semantic_docs = _retrieve_essay_semantic_chunks(query, user_id, top_k)
        if semantic_docs:
            filename = semantic_docs[0].get("filename")
            essay = _essay_store.find_by_filename(user_id, filename) if filename else None
            return semantic_docs, {
                "found": True,
                "essay_id": essay.get("essay_id") if essay else None,
                "title": essay.get("title") if essay else Path(filename or "").stem,
                "filename": filename,
                "retrieval_mode": "semantic_fallback",
                "source": "essay_chunks",
            }

    return [], _empty_essay_context()


def _knowledge_query_from_essay(question: str, essay_docs: List[dict], essay_context: dict) -> str:
    essay_title = essay_context.get("title") or essay_context.get("filename") or ""
    essay_excerpt = "\n\n".join(doc.get("text", "") for doc in essay_docs[:2])
    if not essay_excerpt:
        return question
    return (
        f"用户正在分析自己的随笔《{essay_title}》。\n"
        f"原始提问：{question}\n"
        f"随笔内容摘录：{essay_excerpt[:1800]}\n"
        "请检索有助于理解其中情绪、模式、冲突与认知张力的心理学或哲学知识。"
    )


def _rerank_documents(query: str, docs: List[dict], top_k: int) -> Tuple[List[dict], Dict[str, Any]]:
    docs_with_rank = [{**doc, "rrf_rank": i} for i, doc in enumerate(docs, 1)]
    rerank_api_key = _get_rerank_api_key()
    rerank_endpoint = _get_rerank_endpoint()
    meta: Dict[str, Any] = {
        "rerank_enabled": bool(RERANK_MODEL and rerank_api_key and rerank_endpoint),
        "rerank_applied": False,
        "rerank_model": RERANK_MODEL,
        "rerank_endpoint": rerank_endpoint,
        "rerank_error": None,
        "candidate_count": len(docs_with_rank),
    }
    if not docs_with_rank or not meta["rerank_enabled"]:
        return docs_with_rank[:top_k], meta

    payload = {
        "model": RERANK_MODEL,
        "query": query,
        "documents": [doc.get("text", "") for doc in docs_with_rank],
        "top_n": min(top_k, len(docs_with_rank)),
        "return_documents": False,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {rerank_api_key}",
    }
    try:
        meta["rerank_applied"] = True
        response = requests.post(
            rerank_endpoint,
            headers=headers,
            json=payload,
            timeout=15,
        )
        if response.status_code >= 400:
            meta["rerank_error"] = f"HTTP {response.status_code}: {response.text}"
            return docs_with_rank[:top_k], meta

        items = _extract_rerank_results(response.json())
        reranked = []
        for item in items:
            idx = item.get("index")
            if isinstance(idx, int) and 0 <= idx < len(docs_with_rank):
                doc = dict(docs_with_rank[idx])
                score = item.get("relevance_score")
                if score is not None:
                    doc["rerank_score"] = score
                reranked.append(doc)

        if reranked:
            return reranked[:top_k], meta

        meta["rerank_error"] = "empty_rerank_results"
        return docs_with_rank[:top_k], meta
    except (requests.RequestException, json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        meta["rerank_error"] = str(e)
        return docs_with_rank[:top_k], meta


def _get_stepback_model():
    global _stepback_model
    if not ARK_API_KEY or not MODEL:
        return None
    if _stepback_model is None:
        _stepback_model = init_chat_model(
            model=MODEL,
            model_provider="openai",
            api_key=ARK_API_KEY,
            base_url=BASE_URL,
            temperature=0.2,
        )
    return _stepback_model


def _generate_step_back_question(query: str) -> str:
    model = _get_stepback_model()
    if not model:
        return ""
    prompt = (
        "请将用户的具体问题抽象成更高层次、更概括的‘退步问题’，"
        "用于探寻背后的通用原理或核心概念。只输出退步问题一句话，不要解释。\n"
        f"用户问题：{query}"
    )
    try:
        return (model.invoke(prompt).content or "").strip()
    except Exception:
        return ""


def _answer_step_back_question(step_back_question: str) -> str:
    model = _get_stepback_model()
    if not model or not step_back_question:
        return ""
    prompt = (
        "请简要回答以下退步问题，提供通用原理/背景知识，"
        "控制在120字以内。只输出答案，不要列出推理过程。\n"
        f"退步问题：{step_back_question}"
    )
    try:
        return (model.invoke(prompt).content or "").strip()
    except Exception:
        return ""


def generate_hypothetical_document(query: str) -> str:
    model = _get_stepback_model()
    if not model:
        return ""
    prompt = (
        "请基于用户问题生成一段‘假设性文档’，内容应像真实资料片段，"
        "用于帮助检索相关信息。文档可以包含合理推测，但需与问题语义相关。"
        "只输出文档正文，不要标题或解释。\n"
        f"用户问题：{query}"
    )
    try:
        return (model.invoke(prompt).content or "").strip()
    except Exception:
        return ""


def step_back_expand(query: str) -> dict:
    step_back_question = _generate_step_back_question(query)
    step_back_answer = _answer_step_back_question(step_back_question)
    if step_back_question or step_back_answer:
        expanded_query = (
            f"{query}\n\n"
            f"退步问题：{step_back_question}\n"
            f"退步问题答案：{step_back_answer}"
        )
    else:
        expanded_query = query
    return {
        "step_back_question": step_back_question,
        "step_back_answer": step_back_answer,
        "expanded_query": expanded_query,
    }


def retrieve_documents(
    query: str,
    top_k: int = 5,
    user_id: str | None = None,
    title_hint_query: str | None = None,
    session_context: dict | None = None,
) -> Dict[str, Any]:
    essay_docs, essay_context = _select_essay_from_context(
        query=query,
        user_id=user_id,
        top_k=max(1, min(top_k, 3)),
        title_hint_query=title_hint_query,
        session_context=session_context,
    )

    knowledge_query = query
    if essay_context.get("found"):
        knowledge_query = _knowledge_query_from_essay(query, essay_docs, essay_context)

    if essay_context.get("found") and essay_context.get("source") == "legacy_chunks" and essay_context.get("retrieval_mode") == "exact_title_match":
        return {
            "docs": _dedupe_docs(essay_docs, limit=top_k),
            "meta": {
                "rerank_enabled": False,
                "rerank_applied": False,
                "rerank_model": RERANK_MODEL,
                "rerank_endpoint": _get_rerank_endpoint(),
                "rerank_error": None,
                "retrieval_mode": essay_context.get("retrieval_mode"),
                "candidate_k": len(essay_docs),
                "leaf_retrieve_level": LEAF_RETRIEVE_LEVEL,
                "auto_merge_enabled": AUTO_MERGE_ENABLED,
                "auto_merge_applied": False,
                "auto_merge_threshold": AUTO_MERGE_THRESHOLD,
                "auto_merge_replaced_chunks": 0,
                "auto_merge_steps": 0,
                "essay_context": essay_context,
                "knowledge_context": _empty_knowledge_context(),
            },
        }

    knowledge_result = _retrieve_knowledge_chunks(
        knowledge_query,
        max(2, top_k - len(essay_docs)) if essay_context.get("found") else top_k,
        user_id=user_id,
        include_private_essays=not essay_context.get("found"),
    )
    knowledge_docs = knowledge_result.get("docs", [])
    knowledge_meta = knowledge_result.get("meta", {})

    docs = _dedupe_docs(essay_docs + knowledge_docs, limit=top_k)
    knowledge_context = {
        "found": len(knowledge_docs) > 0,
        "query": knowledge_query,
        "retrieval_mode": knowledge_meta.get("retrieval_mode"),
        "candidate_k": knowledge_meta.get("candidate_k", 0),
        "retrieved_count": len(knowledge_docs),
    }

    return {
        "docs": docs,
        "meta": {
            **knowledge_meta,
            "retrieval_mode": essay_context.get("retrieval_mode") or knowledge_meta.get("retrieval_mode"),
            "essay_context": essay_context,
            "knowledge_context": knowledge_context,
        },
    }
