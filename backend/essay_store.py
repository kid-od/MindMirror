from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

try:
    from database import SessionLocal
    from models import EssayDocument
except ModuleNotFoundError:
    from backend.database import SessionLocal
    from backend.models import EssayDocument


def _normalize_title_key(value: str) -> str:
    stem = Path((value or "").strip()).stem
    return re.sub(r"[\s_\-]+", "", stem).casefold()


def _guess_language(text: str) -> str:
    sample = (text or "").strip()
    if not sample:
        return ""
    if re.search(r"[\u4e00-\u9fff]", sample):
        return "zh"
    if re.search(r"[A-Za-z]", sample):
        return "en"
    return ""


class EssayStore:
    @staticmethod
    def _build_essay_id(owner_id: str, filename: str) -> str:
        payload = f"{(owner_id or '').strip()}::{(filename or '').strip()}".encode("utf-8")
        return hashlib.sha1(payload).hexdigest()

    @staticmethod
    def _to_dict(row: EssayDocument) -> dict:
        return {
            "essay_id": row.essay_id,
            "owner_id": row.owner_id,
            "title": row.title,
            "filename": row.filename,
            "file_type": row.file_type,
            "file_path": row.file_path,
            "language": row.language,
            "content": row.content,
            "chunk_count": row.chunk_count,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }

    def upsert(
        self,
        owner_id: str,
        filename: str,
        content: str,
        file_type: str = "",
        file_path: str = "",
        title: str | None = None,
        language: str | None = None,
        chunk_count: int = 0,
    ) -> dict:
        normalized_owner = (owner_id or "").strip()
        normalized_filename = (filename or "").strip()
        normalized_title = (title or Path(normalized_filename).stem or "Untitled").strip()
        now = datetime.now(UTC).replace(tzinfo=None)
        essay_id = self._build_essay_id(normalized_owner, normalized_filename)

        db = SessionLocal()
        try:
            row = (
                db.query(EssayDocument)
                .filter(
                    EssayDocument.owner_id == normalized_owner,
                    EssayDocument.filename == normalized_filename,
                )
                .first()
            )
            payload = {
                "essay_id": essay_id,
                "owner_id": normalized_owner,
                "title": normalized_title,
                "filename": normalized_filename,
                "file_type": file_type or "",
                "file_path": file_path or "",
                "language": (language or _guess_language(content) or "").strip(),
                "content": content or "",
                "chunk_count": int(chunk_count or 0),
                "updated_at": now,
            }
            if row:
                for key, value in payload.items():
                    setattr(row, key, value)
            else:
                row = EssayDocument(
                    **payload,
                    created_at=now,
                )
                db.add(row)
            db.commit()
            db.refresh(row)
            return self._to_dict(row)
        finally:
            db.close()

    def list_by_owner(self, owner_id: str) -> list[dict]:
        db = SessionLocal()
        try:
            rows = (
                db.query(EssayDocument)
                .filter(EssayDocument.owner_id == (owner_id or "").strip())
                .order_by(EssayDocument.updated_at.desc(), EssayDocument.filename.asc())
                .all()
            )
            return [self._to_dict(row) for row in rows]
        finally:
            db.close()

    def find_by_id(self, owner_id: str, essay_id: str) -> dict | None:
        if not owner_id or not essay_id:
            return None
        db = SessionLocal()
        try:
            row = (
                db.query(EssayDocument)
                .filter(
                    EssayDocument.owner_id == owner_id.strip(),
                    EssayDocument.essay_id == essay_id.strip(),
                )
                .first()
            )
            return self._to_dict(row) if row else None
        finally:
            db.close()

    def find_by_titles(self, owner_id: str, titles: Iterable[str]) -> dict | None:
        normalized_titles = {_normalize_title_key(title) for title in titles if (title or "").strip()}
        if not owner_id or not normalized_titles:
            return None

        db = SessionLocal()
        try:
            rows = (
                db.query(EssayDocument)
                .filter(EssayDocument.owner_id == owner_id.strip())
                .order_by(EssayDocument.updated_at.desc())
                .all()
            )
            for row in rows:
                candidates = {
                    _normalize_title_key(row.title),
                    _normalize_title_key(row.filename),
                }
                if normalized_titles & candidates:
                    return self._to_dict(row)
            return None
        finally:
            db.close()

    def find_by_filename(self, owner_id: str, filename: str) -> dict | None:
        if not owner_id or not filename:
            return None
        db = SessionLocal()
        try:
            row = (
                db.query(EssayDocument)
                .filter(
                    EssayDocument.owner_id == owner_id.strip(),
                    EssayDocument.filename == filename.strip(),
                )
                .first()
            )
            return self._to_dict(row) if row else None
        finally:
            db.close()

    def delete(self, owner_id: str, filename: str) -> dict | None:
        if not owner_id or not filename:
            return None
        db = SessionLocal()
        try:
            row = (
                db.query(EssayDocument)
                .filter(
                    EssayDocument.owner_id == owner_id.strip(),
                    EssayDocument.filename == filename.strip(),
                )
                .first()
            )
            if not row:
                return None
            payload = self._to_dict(row)
            db.delete(row)
            db.commit()
            return payload
        finally:
            db.close()
