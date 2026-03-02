import hashlib
import json
import logging

logger = logging.getLogger(__name__)

_cache: dict[str, dict] = {}
_data_version: int = 0


def bump_version() -> None:
    """Called after successful ingest to invalidate all cached themes."""
    global _data_version
    _data_version += 1
    logger.info("Theme cache version bumped to %d", _data_version)


def get_cached(params: dict) -> dict | None:
    """Return cached response dict if params match and no new ingest has occurred."""
    key = _make_key(params)
    entry = _cache.get(key)
    if entry and entry["version"] == _data_version:
        logger.info("Theme cache hit for key %s", key[:8])
        return entry["data"]
    return None


def set_cached(params: dict, data: dict) -> None:
    """Store a themes response dict in the cache."""
    key = _make_key(params)
    _cache[key] = {"version": _data_version, "data": data}
    logger.info("Theme cache set for key %s (version %d)", key[:8], _data_version)


def _make_key(params: dict) -> str:
    return hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
