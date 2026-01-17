from pathlib import Path
import redis
from typing import Any

from generic_api_client.models.cache import CacheTree, TargetCache
from generic_api_client.models.requests import Response
from generic_api_client.models.target import Target


class CacheService:
    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 300) -> None:
        self.redis = redis_client
        self.ttl = ttl_seconds

    # Private Methods

    def _get_target_cache(self, target: Target) -> TargetCache | None:
        """Return the TargetCache associated to a target."""
        cache_res = self.redis.get(target.sig())
        return TargetCache.model_validate_json(cache_res) if cache_res else None

    def _create_target_cache(self, target: Target) -> TargetCache:
        """Create a TargetCache using target then return the TargetCache created."""
        target_cache = TargetCache(auth_data=target.auth_data, responses_tree=CacheTree())
        self._set_target_cache(target, target_cache)
        return target_cache

    def _set_target_cache(self, target: Target, target_cache: TargetCache) -> None:
        """Set the TargetCache for a target"""
        self.redis.set(target.sig(), target_cache.model_dump_json(), ex=self.ttl)

    # Public Methods

    def get(self, target: Target, template_path: Path, request_args: dict[str, Any]) -> Response | None:
        """Get a cache entry using the target, the request args and the template path"""
        target_cache = self._get_target_cache(target)
        return None if not target_cache else target_cache.get_response(template_path, request_args)

    def set(self, target: Target, template_path: Path, request_args: dict[str, Any], response: Response) -> None:
        """Set a cache entry using the target, the request args and the template path and the response"""
        # set the response on the target_cache
        target_cache = self._get_target_cache(target) or self._create_target_cache(target)
        target_cache.set_response(template_path, request_args, response)
        # Update the target
        self._set_target_cache(target, target_cache)

    def delete_cache_response(self, target: Target, template_path: Path, request_args: dict[str, Any]) -> None:
        """Clear a cache entry using the target, the request args and the template path"""
        target_cache = self._get_target_cache(target)
        if target_cache:
            target_cache.delete_response(template_path, request_args)

    def delete_cache_target(self, target: Target) -> None:
        """Clear a cache target using the target"""
        self.redis.delete(target.sig())

    def clear(self) -> None:
        """Clear all the cache"""
        self.redis.flushdb()
