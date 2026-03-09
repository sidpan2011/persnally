"""Simple TTL cache for API responses. Avoids hitting rate limits on repeated queries."""

import time
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}
DEFAULT_TTL = 3600  # 1 hour


def cache_get(key: str) -> Any | None:
    if key in _cache:
        expiry, value = _cache[key]
        if time.time() < expiry:
            return value
        del _cache[key]
    return None


def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    _cache[key] = (time.time() + ttl, value)


def cache_key(*parts: str) -> str:
    return ":".join(str(p) for p in parts)
