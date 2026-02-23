import time
import json
import asyncio
from typing import Dict, Optional, Any
from app.cache.interface import CacheInterface

class MemoryCache(CacheInterface):
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._expires: Dict[str, float] = {}
        self._lock = asyncio.Lock() # Use asyncio lock, not threading lock

    def _is_expired(self, key: str) -> bool:
        if key in self._expires and time.time() > self._expires[key]:
            return True
        return False

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if self._is_expired(key):
                self._store.pop(key, None)
                self._expires.pop(key, None)
                return None
            return self._store.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            self._store[key] = value
            if ttl:
                self._expires[key] = time.time() + ttl
            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            self._store.pop(key, None)
            self._expires.pop(key, None)
            return True

    async def exists(self, key: str) -> bool:
        async with self._lock:
            return key in self._store and not self._is_expired(key)

    async def increment(self, key: str, amount: int = 1) -> int:
        async with self._lock:
            current = self._store.get(key, 0)
            if not isinstance(current, int):
                current = 0
            new_val = current + amount
            self._store[key] = new_val
            return new_val

    async def clear(self) -> bool:
        async with self._lock:
            self._store.clear()
            self._expires.clear()
            return True
