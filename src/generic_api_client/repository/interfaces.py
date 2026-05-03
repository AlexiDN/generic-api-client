from abc import ABC, abstractmethod


class CacheRepository(ABC):
    ttl_seconds: int

    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds

    @abstractmethod
    def get(self, key: str) -> str | None:
        """Get cached key"""

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Cache a value based on key"""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a cached key"""

    @abstractmethod
    def clear(self) -> None:
        """Clear the cache"""
