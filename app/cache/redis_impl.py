import json
import redis.asyncio as redis
from typing import Optional, Any
from app.cache.interface import CacheInterface

class RedisCache(CacheInterface):
    def __init__(self, host: str, port: int, db: int):
        # Redis.from_url or direct init both support pooling in async mode
        self._client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )

    async def get(self, key: str) -> Optional[Any]:
        data = await self._client.get(key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        # Avoid double-serializing strings
        serialized = json.dumps(value) if not isinstance(value, (str, int, float)) else value
        return await self._client.set(key, serialized, ex=ttl)

    async def delete(self, key: str) -> bool:
        return bool(await self._client.delete(key))

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(key))

    async def increment(self, key: str, amount: int = 1) -> int:
        return await self._client.incrby(key, amount)

    async def clear(self) -> bool:
        return await self._client.flushdb()

    async def close(self):
        """Important for clean shutdown in FastAPI"""
        await self._client.close()
