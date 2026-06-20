from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import re


_STOPWORDS = {
    "about",
    "again",
    "chat",
    "daily",
    "essay",
    "from",
    "have",
    "into",
    "review",
    "session",
    "that",
    "this",
    "with",
    "your",
}


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_theme_terms(*values: str) -> list[str]:
    tokens: list[str] = []
    for value in values:
        for token in re.findall(r"[A-Za-z]{4,}|[\u4e00-\u9fff]{2,}", value or ""):
            normalized = token.casefold()
            if normalized in _STOPWORDS:
                continue
            tokens.append(normalized)
    return tokens


def list_public_document_activity() -> list[dict]:
    try:
        from database import SessionLocal
        from models import ParentChunk
    except ModuleNotFoundError:
        from backend.database import SessionLocal
        from backend.models import ParentChunk

    db = SessionLocal()
    try:
        rows = db.query(ParentChunk).filter(
            ParentChunk.visibility == "public",
            ParentChunk.document_domain == "knowledge_base",
        ).all()

        by_file: dict[str, dict] = {}
        for row in rows:
            if row.filename not in by_file:
                by_file[row.filename] = {
                    "filename": row.filename,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
                continue

            current = _parse_timestamp(by_file[row.filename]["updated_at"])
            candidate = row.updated_at
            if candidate and (current is None or candidate > current):
                by_file[row.filename]["updated_at"] = candidate.isoformat()

        return sorted(by_file.values(), key=lambda item: item.get("updated_at") or "", reverse=True)
    finally:
        db.close()


def build_insights_payload(essays: list[dict], sessions: list[dict], documents: list[dict] | None = None) -> dict:
    documents = documents or []
    # insights 页只做轻量聚合：主题词、最近活动和最近内容，不引入新的持久化结构。
    theme_counter: Counter[str] = Counter()
    activity = defaultdict(lambda: {"essays": 0, "sessions": 0, "documents": 0})

    for essay in essays:
        theme_counter.update(_extract_theme_terms(essay.get("title", ""), Path(essay.get("filename", "")).stem))
        stamp = _parse_timestamp(essay.get("uploaded_at"))
        if stamp:
            activity[stamp.date().isoformat()]["essays"] += 1

    for session in sessions:
        theme_counter.update(_extract_theme_terms(session.get("title", "")))
        stamp = _parse_timestamp(session.get("updated_at"))
        if stamp:
            activity[stamp.date().isoformat()]["sessions"] += 1

    for document in documents:
        stamp = _parse_timestamp(document.get("updated_at"))
        if stamp:
            activity[stamp.date().isoformat()]["documents"] += 1

    recent_essays = sorted(essays, key=lambda item: item.get("uploaded_at") or "", reverse=True)[:3]
    recent_sessions = sorted(sessions, key=lambda item: item.get("updated_at") or "", reverse=True)[:3]

    return {
        "totals": {
            "essays": len(essays),
            "sessions": len(sessions),
            "documents": len(documents),
        },
        "top_themes": [{"label": label, "count": count} for label, count in theme_counter.most_common(6)],
        "activity": [
            {"date": date, **counts}
            for date, counts in sorted(activity.items(), key=lambda pair: pair[0])
        ],
        "recent_essays": recent_essays,
        "recent_sessions": recent_sessions,
    }


def build_timeline_payload(essays: list[dict], sessions: list[dict], documents: list[dict] | None = None) -> dict:
    documents = documents or []
    events: list[dict] = []

    for essay in essays:
        timestamp = essay.get("uploaded_at")
        if timestamp:
            events.append(
                {
                    "kind": "essay",
                    "timestamp": timestamp,
                    "title": essay.get("title") or Path(essay.get("filename", "")).stem,
                    "subtitle": essay.get("filename", ""),
                    "reference": essay.get("essay_id"),
                }
            )

    for session in sessions:
        timestamp = session.get("updated_at")
        if timestamp:
            events.append(
                {
                    "kind": "session",
                    "timestamp": timestamp,
                    "title": session.get("title") or session.get("session_id", ""),
                    "subtitle": f'{session.get("message_count", 0)} messages',
                    "reference": session.get("session_id"),
                }
            )

    for document in documents:
        timestamp = document.get("updated_at")
        if timestamp:
            events.append(
                {
                    "kind": "document",
                    "timestamp": timestamp,
                    "title": document.get("filename", ""),
                    "subtitle": "Knowledge base update",
                    "reference": document.get("filename"),
                }
            )

    events.sort(key=lambda item: item["timestamp"], reverse=True)

    groups: list[dict] = []
    current_group: dict | None = None
    for event in events:
        # 前端按天展示时间线，这里直接预分组，避免客户端重复做日期归并。
        date_key = event["timestamp"][:10]
        if current_group is None or current_group["date"] != date_key:
            current_group = {"date": date_key, "items": []}
            groups.append(current_group)
        current_group["items"].append(event)

    return {"groups": groups}
