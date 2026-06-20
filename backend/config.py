import re


_URL_WITH_ENV_PREFIX_RE = re.compile(r"^[A-Z0-9_]+=(https?://.+)$", re.IGNORECASE)
DEFAULT_CORS_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]


def normalize_base_url(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    match = _URL_WITH_ENV_PREFIX_RE.match(cleaned)
    if match:
        return match.group(1)

    return cleaned


def resolve_grade_model(model: str | None, grade_model: str | None, default: str = "qwen3.6-plus") -> str:
    """Resolve the model used by the RAG relevance grader."""
    for candidate in (grade_model, model, default):
        if candidate and candidate.strip():
            return candidate.strip()

    return default


def parse_cors_origins(value: str | None) -> list[str]:
    origins = [item.strip() for item in (value or "").split(",") if item.strip()]
    return origins or list(DEFAULT_CORS_ORIGINS)
