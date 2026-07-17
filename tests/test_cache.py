import time
from backend.utils.cache import ResponseCache


def test_cache_set_get():
    cache = ResponseCache(ttl_seconds=2)
    cache.set("prompt1", value="response1")
    assert cache.get("prompt1") == "response1"

def test_cache_miss():
    cache = ResponseCache(ttl_seconds=2)
    assert cache.get("prompt2") is None

def test_cache_expiration():
    cache = ResponseCache(ttl_seconds=1)
    cache.set("prompt1", value="response1")
    time.sleep(1.5)
    assert cache.get("prompt1") is None
