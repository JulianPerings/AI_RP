"""Redis cache service for session management and caching."""

import json
from typing import Optional, Any
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import log


class CacheService:
    """Async Redis cache service."""

    def __init__(self):
        """Initialize Redis connection."""
        self.redis: Optional[redis.Redis] = None
        self.default_ttl = settings.redis_cache_ttl

    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            log.info("Connected to Redis")
        except Exception as e:
            log.error(f"Failed to connect to Redis: {str(e)}")
            raise

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            log.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            log.error(f"Cache get error for key {key}: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        try:
            serialized = json.dumps(value)
            await self.redis.set(
                key,
                serialized,
                ex=ttl or self.default_ttl
            )
            return True
        except Exception as e:
            log.error(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Success status
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            log.error(f"Cache delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            Existence status
        """
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            log.error(f"Cache exists error for key {key}: {str(e)}")
            return False

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get game session data."""
        return await self.get(f"session:{session_id}")

    async def set_session(
        self,
        session_id: str,
        session_data: dict,
        ttl: int = 3600
    ) -> bool:
        """Set game session data."""
        return await self.set(f"session:{session_id}", session_data, ttl)

    async def delete_session(self, session_id: str) -> bool:
        """Delete game session."""
        return await self.delete(f"session:{session_id}")


# Global cache service instance
cache_service = CacheService()
