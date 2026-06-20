"""Upload file helpers shared by API handlers."""

SUPPORTED_UPLOAD_EXTENSIONS = (
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".md",
    ".markdown",
)


def validate_upload_filename(filename: str) -> str:
    cleaned = (filename or "").strip()
    file_lower = cleaned.lower()
    if not cleaned:
        raise ValueError("文件名不能为空")
    if "/" in cleaned or "\\" in cleaned or cleaned in {".", ".."}:
        raise ValueError("文件名不能包含路径")
    if not file_lower.endswith(SUPPORTED_UPLOAD_EXTENSIONS):
        raise ValueError("仅支持 PDF、Word、Excel 和 Markdown 文档")
    return file_lower


def collect_upload_files(file=None, files=None) -> list:
    collected = []
    if files:
        collected.extend(item for item in files if item is not None)
    if file is not None:
        collected.append(file)
    return collected
