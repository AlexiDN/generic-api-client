from .interfaces import CacheRepository
from expiring_dict import ExpiringDict


class ExpiringDictCacheRepository(CacheRepository):
    def __init__(self, ttl_seconds: int) -> None:
        super().__init__(ttl_seconds)
        self._store = ExpiringDict(ttl_seconds)

    def _keys(self) -> list[str]:
        """Return the keys in cache"""
        return list(self._store)

    def get(self, key: str) -> str | None:
        """Get cached key"""
        return self._store[key] if key in self._keys() else None

    def set(self, key: str, value: str) -> None:
        """Cache a value based on key"""
        self._store[key] = value

    def delete(self, key: str) -> None:
        """Delete a cached key"""
        if key in self._keys():
            del self._store[key]

    def clear(self) -> None:
        """Clear the cache"""
        for key in self._keys():
            del self._store[key]
