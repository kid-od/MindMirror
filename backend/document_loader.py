"""文档加载和分片服务。

公共知识库采用“三层分块”：父级 chunk 存 PostgreSQL，叶子 chunk 写 Milvus 做召回；
私密随笔则保留完整正文，并按 Milvus 文本长度限制切成可检索片段。
"""
import os
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader

try:
    from text_utils import sanitize_text
except ModuleNotFoundError:
    from backend.text_utils import sanitize_text

try:
    from upload_files import SUPPORTED_UPLOAD_EXTENSIONS
except ModuleNotFoundError:
    from backend.upload_files import SUPPORTED_UPLOAD_EXTENSIONS


class DocumentLoader:
    """把不同格式的文档统一转换成带元数据的 chunk 列表。"""
    _MILVUS_TEXT_MAX_BYTES = 2000
    _ESSAY_TARGET_BYTES = 1800
    _ESSAY_BREAKPOINTS = {"\n", "。", "！", "？", "；", "，", "、", " ", ".", "!", "?", ";", ","}

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        # 保留原有参数以兼容外部调用；默认启用三层滑动窗口分块。
        level_1_size = max(1200, chunk_size * 2)
        level_1_overlap = max(240, chunk_overlap * 2)
        level_2_size = max(600, chunk_size)
        level_2_overlap = max(120, chunk_overlap)
        level_3_size = max(300, chunk_size // 2)
        level_3_overlap = max(60, chunk_overlap // 2)

        self._splitter_level_1 = RecursiveCharacterTextSplitter(
            chunk_size=level_1_size,
            chunk_overlap=level_1_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", "。", "！", "？", "，", "、", " ", ""],
        )
        self._splitter_level_2 = RecursiveCharacterTextSplitter(
            chunk_size=level_2_size,
            chunk_overlap=level_2_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", "。", "！", "？", "，", "、", " ", ""],
        )
        self._splitter_level_3 = RecursiveCharacterTextSplitter(
            chunk_size=level_3_size,
            chunk_overlap=level_3_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", "。", "！", "？", "，", "、", " ", ""],
        )
        self._essay_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max(1400, chunk_size * 2),
            chunk_overlap=max(160, chunk_overlap * 2),
            add_start_index=True,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", "、", " ", ""],
        )

    @staticmethod
    def _build_chunk_scope_prefix(base_doc: Dict) -> str:
        """为私密或非默认作用域的 chunk_id 添加前缀，避免不同用户同名文件冲突。"""
        visibility = (base_doc.get("visibility") or "public").strip().lower()
        owner_id = (base_doc.get("owner_id") or "").strip()
        document_domain = (base_doc.get("document_domain") or "knowledge_base").strip().lower()
        if visibility == "public" and not owner_id and document_domain == "knowledge_base":
            return ""

        safe_visibility = re.sub(r"[^A-Za-z0-9._-]+", "_", visibility) or "public"
        safe_owner = re.sub(r"[^A-Za-z0-9._-]+", "_", owner_id) or "anonymous"
        safe_domain = re.sub(r"[^A-Za-z0-9._-]+", "_", document_domain) or "default"
        return f"{safe_visibility}::{safe_owner}::{safe_domain}::"

    @staticmethod
    def _build_chunk_id(filename: str, page_number: int, level: int, index: int, scope_prefix: str = "") -> str:
        return f"{scope_prefix}{filename}::p{page_number}::l{level}::{index}"

    def _split_page_to_three_levels(
        self,
        text: str,
        base_doc: Dict,
        page_global_chunk_idx: int,
    ) -> List[Dict]:
        """将单页文本拆成 L1/L2/L3 三层 chunk，保留父子关系用于 auto-merging。"""
        text = sanitize_text(text).strip()
        if not text:
            return []

        root_chunks: List[Dict] = []
        page_number = int(base_doc.get("page_number", 0))
        filename = base_doc["filename"]
        scope_prefix = self._build_chunk_scope_prefix(base_doc)

        level_1_docs = self._splitter_level_1.create_documents([text], [base_doc])
        level_1_counter = 0
        level_2_counter = 0
        level_3_counter = 0

        for level_1_doc in level_1_docs:
            level_1_text = sanitize_text(level_1_doc.page_content).strip()
            if not level_1_text:
                continue
            level_1_id = self._build_chunk_id(filename, page_number, 1, level_1_counter, scope_prefix=scope_prefix)
            level_1_counter += 1

            level_1_chunk = {
                **base_doc,
                "text": level_1_text,
                "chunk_id": level_1_id,
                "parent_chunk_id": "",
                "root_chunk_id": level_1_id,
                "chunk_level": 1,
                "chunk_idx": page_global_chunk_idx,
            }
            page_global_chunk_idx += 1
            root_chunks.append(level_1_chunk)

            level_2_docs = self._splitter_level_2.create_documents([level_1_text], [base_doc])
            for level_2_doc in level_2_docs:
                level_2_text = sanitize_text(level_2_doc.page_content).strip()
                if not level_2_text:
                    continue
                level_2_id = self._build_chunk_id(filename, page_number, 2, level_2_counter, scope_prefix=scope_prefix)
                level_2_counter += 1

                level_2_chunk = {
                    **base_doc,
                    "text": level_2_text,
                    "chunk_id": level_2_id,
                    "parent_chunk_id": level_1_id,
                    "root_chunk_id": level_1_id,
                    "chunk_level": 2,
                    "chunk_idx": page_global_chunk_idx,
                }
                page_global_chunk_idx += 1
                root_chunks.append(level_2_chunk)

                level_3_docs = self._splitter_level_3.create_documents([level_2_text], [base_doc])
                for level_3_doc in level_3_docs:
                    level_3_text = sanitize_text(level_3_doc.page_content).strip()
                    if not level_3_text:
                        continue
                    level_3_id = self._build_chunk_id(filename, page_number, 3, level_3_counter, scope_prefix=scope_prefix)
                    level_3_counter += 1
                    root_chunks.append({
                        **base_doc,
                        "text": level_3_text,
                        "chunk_id": level_3_id,
                        "parent_chunk_id": level_2_id,
                        "root_chunk_id": level_1_id,
                        "chunk_level": 3,
                        "chunk_idx": page_global_chunk_idx,
                    })
                    page_global_chunk_idx += 1

        return root_chunks

    @classmethod
    def _utf8_len(cls, text: str) -> int:
        return len((text or "").encode("utf-8"))

    @classmethod
    def _split_text_by_max_bytes(cls, text: str, max_bytes: int) -> List[str]:
        """按 UTF-8 字节数切分文本，优先在中文标点或空白处断开。"""
        cleaned = sanitize_text(text).strip()
        if not cleaned:
            return []
        if cls._utf8_len(cleaned) <= max_bytes:
            return [cleaned]

        chunks: List[str] = []
        start = 0
        length = len(cleaned)
        while start < length:
            byte_count = 0
            idx = start
            last_break = -1
            while idx < length:
                char = cleaned[idx]
                char_bytes = len(char.encode("utf-8"))
                if byte_count + char_bytes > max_bytes:
                    break
                byte_count += char_bytes
                if char in cls._ESSAY_BREAKPOINTS:
                    last_break = idx + 1
                idx += 1

            if idx >= length:
                piece = cleaned[start:length].strip()
                if piece:
                    chunks.append(piece)
                break

            split_at = last_break if last_break > start else idx
            piece = cleaned[start:split_at].strip()
            if not piece:
                split_at = min(length, start + 1)
                piece = cleaned[start:split_at].strip()
            if piece:
                chunks.append(piece)
            start = split_at

        return [chunk for chunk in chunks if chunk]

    @classmethod
    def _enforce_text_byte_limit(cls, chunks: List[str], max_bytes: int | None = None) -> List[str]:
        """确保随笔 chunk 不超过 Milvus VARCHAR 字段的字节上限。"""
        limit = max_bytes or cls._ESSAY_TARGET_BYTES
        enforced: List[str] = []
        for chunk in chunks:
            enforced.extend(cls._split_text_by_max_bytes(chunk, max_bytes=limit))
        return [item for item in enforced if item and cls._utf8_len(item) <= cls._MILVUS_TEXT_MAX_BYTES]

    @staticmethod
    def _resolve_doc_type(filename: str):
        file_lower = filename.lower()
        if file_lower.endswith(".pdf"):
            return "PDF", PyPDFLoader
        if file_lower.endswith((".docx", ".doc")):
            return "Word", Docx2txtLoader
        if file_lower.endswith((".xlsx", ".xls")):
            return "Excel", UnstructuredExcelLoader
        if file_lower.endswith((".md", ".markdown")):
            return "Markdown", None
        raise ValueError(f"不支持的文件类型: {filename}")

    def _load_raw_documents(self, file_path: str, filename: str):
        doc_type, loader_cls = self._resolve_doc_type(filename)
        if doc_type == "Markdown":
            text = Path(file_path).read_text(encoding="utf-8-sig", errors="replace")
            return doc_type, [SimpleNamespace(page_content=text, metadata={"page": 0})]
        loader = loader_cls(file_path)
        return doc_type, loader.load()

    def load_document_content(self, file_path: str, filename: str) -> dict:
        try:
            doc_type, raw_docs = self._load_raw_documents(file_path, filename)
            parts = []
            for doc in raw_docs:
                cleaned = sanitize_text(doc.page_content).strip()
                if cleaned:
                    parts.append(cleaned)
            content = "\n\n".join(parts).strip()
            return {
                "content": content,
                "file_type": doc_type,
            }
        except Exception as e:
            raise Exception(f"处理文档失败: {str(e)}")

    def load_essay_document(
        self,
        file_path: str,
        filename: str,
        metadata: dict | None = None,
        full_text_threshold: int = 2800,
    ) -> dict:
        """加载私密随笔，并同时返回完整正文与可检索 chunk。"""
        metadata = metadata or {}
        extracted = self.load_document_content(file_path, filename)
        content = sanitize_text(extracted.get("content", "")).strip()
        file_type = extracted.get("file_type", "")
        if not content:
            return {"content": "", "file_type": file_type, "chunks": []}

        base_doc = {
            "filename": filename,
            "file_path": file_path,
            "file_type": file_type,
            "page_number": 0,
            "visibility": metadata.get("visibility", "private"),
            "owner_id": metadata.get("owner_id", ""),
            "document_domain": metadata.get("document_domain", "essay"),
        }
        scope_prefix = self._build_chunk_scope_prefix(base_doc)

        raw_segments: List[str] = []
        if len(content) <= full_text_threshold:
            raw_segments = [content]
        else:
            for doc in self._essay_splitter.create_documents([content], [base_doc]):
                text = sanitize_text(doc.page_content).strip()
                if text:
                    raw_segments.append(text)
        safe_segments = self._enforce_text_byte_limit(raw_segments)

        chunks = []
        for idx, text in enumerate(safe_segments):
            chunk_id = self._build_chunk_id(filename, 0, 1, idx, scope_prefix=scope_prefix)
            chunks.append(
                {
                    **base_doc,
                    "text": text,
                    "chunk_id": chunk_id,
                    "parent_chunk_id": "",
                    "root_chunk_id": chunk_id,
                    "chunk_level": 1,
                    "chunk_idx": idx,
                }
            )

        return {
            "content": content,
            "file_type": file_type,
            "chunks": chunks,
        }

    def load_document(self, file_path: str, filename: str, metadata: dict | None = None) -> list[dict]:
        """
        加载单个文档并分片
        :param file_path: 文件路径
        :param filename: 文件名
        :param metadata: 追加到每个 chunk 的作用域元数据
        :return: 分片后的文档列表
        """
        metadata = metadata or {}
        try:
            doc_type, raw_docs = self._load_raw_documents(file_path, filename)
            documents = []
            page_global_chunk_idx = 0
            for doc in raw_docs:
                base_doc = {
                    "filename": filename,
                    "file_path": file_path,
                    "file_type": doc_type,
                    "page_number": doc.metadata.get("page", 0),
                    "visibility": metadata.get("visibility", "public"),
                    "owner_id": metadata.get("owner_id", ""),
                    "document_domain": metadata.get("document_domain", "knowledge_base"),
                }
                page_chunks = self._split_page_to_three_levels(
                    text=sanitize_text(doc.page_content).strip(),
                    base_doc=base_doc,
                    page_global_chunk_idx=page_global_chunk_idx,
                )
                page_global_chunk_idx += len(page_chunks)
                documents.extend(page_chunks)
            return documents
        except Exception as e:
            raise Exception(f"处理文档失败: {str(e)}")

    def load_documents_from_folder(self, folder_path: str, metadata: dict | None = None) -> list[dict]:
        """
        从文件夹加载所有文档并分片
        :param folder_path: 文件夹路径
        :param metadata: 追加到每个 chunk 的作用域元数据
        :return: 所有分片后的文档列表
        """
        all_documents = []

        for filename in os.listdir(folder_path):
            file_lower = filename.lower()
            if not file_lower.endswith(SUPPORTED_UPLOAD_EXTENSIONS):
                continue

            file_path = os.path.join(folder_path, filename)
            try:
                documents = self.load_document(file_path, filename, metadata=metadata)
                all_documents.extend(documents)
            except Exception:
                continue

        return all_documents
