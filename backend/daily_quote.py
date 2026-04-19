from __future__ import annotations

import json
import random
import urllib.error
import urllib.parse
import urllib.request
from datetime import date


_FALLBACK_QUOTES = {
    "zh": [
        {
            "text": "允许自己慢一点，也是在认真地活着。",
            "author": "PsycheArchive",
            "language": "zh",
            "source": "local",
            "fallback": True,
        },
        {
            "text": "看见自己的感受，不等于被它吞没。",
            "author": "PsycheArchive",
            "language": "zh",
            "source": "local",
            "fallback": True,
        },
        {
            "text": "很多答案不会立刻出现，但诚实地提问本身就是开始。",
            "author": "PsycheArchive",
            "language": "zh",
            "source": "local",
            "fallback": True,
        },
    ],
    "en": [
        {
            "text": "You are allowed to move slowly and still be growing.",
            "author": "PsycheArchive",
            "language": "en",
            "source": "local",
            "fallback": True,
        },
        {
            "text": "Noticing your feelings is already a form of courage.",
            "author": "PsycheArchive",
            "language": "en",
            "source": "local",
            "fallback": True,
        },
        {
            "text": "A gentler question can open a deeper truth.",
            "author": "PsycheArchive",
            "language": "en",
            "source": "local",
            "fallback": True,
        },
    ],
}

_QUOTE_CACHE: dict[tuple[str, str], dict] = {}


def normalize_quote_payload(payload: dict | list, source: str) -> dict:
    if source == "zenquotes":
        row = payload[0] if isinstance(payload, list) and payload else {}
        return {
            "text": (row.get("q") or "").strip(),
            "author": (row.get("a") or "Unknown").strip(),
            "language": "en",
            "source": source,
            "fallback": False,
        }

    if source == "theysaidso":
        row = (((payload or {}).get("contents") or {}).get("quotes") or [{}])[0]
        return {
            "text": (row.get("quote") or "").strip(),
            "author": (row.get("author") or "Unknown").strip(),
            "language": "en",
            "source": source,
            "fallback": False,
        }

    raise ValueError(f"Unsupported quote source: {source}")


def pick_fallback_quote(locale: str = "zh") -> dict:
    language = "zh" if locale == "zh" else "en"
    return dict(random.choice(_FALLBACK_QUOTES[language]))


def _fetch_json(url: str) -> dict | list:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PsycheArchive/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset)
        return json.loads(body)


def fetch_remote_quote() -> dict:
    sources = [
        ("zenquotes", "https://zenquotes.io/api/today"),
        ("theysaidso", "https://quotes.rest/qod?category=inspire"),
    ]

    for source, url in sources:
        try:
            quote = normalize_quote_payload(_fetch_json(url), source=source)
            if quote.get("text"):
                return quote
        except (ValueError, KeyError, IndexError, TypeError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            continue

    raise RuntimeError("No remote quote source available")


def get_daily_quote(locale: str = "zh") -> dict:
    normalized_locale = "zh" if locale == "zh" else "en"
    cache_key = (date.today().isoformat(), normalized_locale)
    cached = _QUOTE_CACHE.get(cache_key)
    if cached:
        return dict(cached)

    try:
        quote = fetch_remote_quote()
    except RuntimeError:
        quote = pick_fallback_quote(normalized_locale)

    _QUOTE_CACHE[cache_key] = dict(quote)
    return dict(quote)
