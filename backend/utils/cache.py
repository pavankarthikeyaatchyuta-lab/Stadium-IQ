"""
Caching utility for StadiumIQ to improve efficiency and reduce AI API calls.
Implements an in-memory MD5-hashed ResponseCache.
"""
import hashlib
import json
import time
from typing import Any

from backend.config import CACHE_TTL_SECONDS


class ResponseCache:
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self._store: dict[str, dict[str, Any]] = {}
        self.ttl = ttl_seconds

    def _key(self, *args) -> str:
        """Generate an MD5 hash key from the arguments."""
        raw = json.dumps(args, sort_keys=True, default=str)
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, *args) -> Any | None:
        """Retrieve a cached value if it hasn't expired."""
        key = self._key(*args)
        entry = self._store.get(key)
        if entry and time.time() - entry["time"] < self.ttl:
            return entry["value"]
        return None

    def set(self, *args, value: Any) -> None:
        """Store a value in the cache with the current timestamp."""
        key = self._key(*args)
        self._store[key] = {"value": value, "time": time.time()}

# Global cache instance for the application
gemini_cache = ResponseCache()
