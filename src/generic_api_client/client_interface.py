from typing import get_type_hints

from redis import Redis
from generic_api_client.api_segments import APIAggregate
from generic_api_client.models.target import Target
from generic_api_client.repository.expiring_dict import ExpiringDictCacheRepository
from generic_api_client.repository.redis import RedisCacheRepository
from generic_api_client.services.cache_service import CacheService


class ClientInterface:
    """A base class to build your Client.
    Your subclass need to redefine the field segments with a proper custom implementation of APIAggregate
    """

    segments: APIAggregate

    def __init__(self, cache_ttl_seconds: int = 60, redis_client: Redis | None = None) -> None:
        """Create the instance client.
        cache_ttl_seconds: ttl of cache entries
        redis_client: redis client to use for cache
        """
        # Create CacheService
        cache_repository = (
            RedisCacheRepository(redis_client, ttl_seconds=cache_ttl_seconds)
            if redis_client
            else ExpiringDictCacheRepository(ttl_seconds=cache_ttl_seconds)
        )
        cache_service = CacheService(repository=cache_repository)
        # Init segments
        segments_class = get_type_hints(self).get("segments")
        if segments_class == APIAggregate:
            msg = (
                f"Can't create {self.__class__} because field 'segments' is not typed properly."
                "You need to properly create a custom APIAggregate class."
            )
            raise RuntimeError(msg)
        self.segments = segments_class(cache_service=cache_service)

    def set_target(self, target: Target, extract_version: bool = False) -> None:
        """Set the connector target.
        If extract_version is True, extract the version of the target to configure segments
        """
        self.segments.set_target(target, get_version=extract_version)
