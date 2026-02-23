from typing import Optional
from app.cache.interface import CacheInterface
from app.cache.redis_impl import RedisCache
from app.cache.memory_impl import MemoryCache
from app.core.config import settings

class CacheService:
    _instance: Optional[CacheInterface] = None

    @classmethod
    def get_instance(cls) -> CacheInterface:
        if cls._instance is None:
            # Fallback for unexpected access before initialization
            cls.initialize()
        return cls._instance

    @classmethod
    def initialize(cls):
        """Dynamically initialize the cache based on environment settings."""
        if settings.cache_type.lower() == "redis":
            cls._instance = RedisCache(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db
            )
        else:
            cls._instance = MemoryCache()

    @classmethod
    async def close(cls):
        """Gracefully close connections if the implementation supports it."""
        if cls._instance and hasattr(cls._instance, 'close'):
            await cls._instance.close()
        cls._instance = None

# Shortcut for dependency injection
def get_cache() -> CacheInterface:
    return CacheService.get_instance()
