import redis

from .interfaces import CacheRepository


class RedisCacheRepository(CacheRepository):
    def __init__(self, client: redis.Redis, ttl_seconds: int) -> None:
        super().__init__(ttl_seconds)
        self._client = client
        try:
            self._client.ping()
        except redis.exceptions.ConnectionError as e:
            msg = f"Can't initiate connection with Redis cache repository. Caused by {e}"
            raise RuntimeError(msg) from e

        self._ttl = ttl_seconds

    def get(self, key: str) -> str | None:
        """Get a cached key from Redis"""
        return self._client.get(key)

    def set(self, key: str, value: str) -> None:
        """Cache a value to Redis"""
        self._client.set(key, value, ex=self._ttl)

    def delete(self, key: str) -> None:
        """Delete a cached key from Redis"""
        self._client.delete(key)

    def clear(self) -> None:
        """Clear the cache from Redis"""
        self._client.flushdb()
