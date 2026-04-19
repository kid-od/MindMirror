"""Text normalization helpers shared by document ingestion components."""


def sanitize_text(value: object) -> str:
    """Return text safe for PostgreSQL and vector-store metadata fields."""
    if value is None:
        return ""

    return str(value).replace("\x00", "")
