from copy import deepcopy
from pathlib import Path

from generic_api_client.models.cache import CacheResponse, CacheTree, TargetCache
from generic_api_client.models.requests import Response
from generic_api_client.models.target import Target
from generic_api_client.repository.interfaces import CacheRepository
from generic_api_client.utils import JSONType, ResponseSource, get_current_time


class CacheService:
    def __init__(self, repository: CacheRepository) -> None:
        self._repo = repository

    # Private Methods

    def _get_target_cache(self, target: Target) -> TargetCache | None:
        """Return the TargetCache associated to a target."""
        cache_res = self._repo.get(target.sig())
        return TargetCache.model_validate_json(cache_res) if cache_res else None

    def _create_target_cache(self, target: Target) -> TargetCache:
        """Create a TargetCache using target then return the TargetCache created."""
        target_cache = TargetCache(auth_data=target.auth_data, responses_tree=CacheTree())
        self._set_target_cache(target, target_cache)
        return target_cache

    def _set_target_cache(self, target: Target, target_cache: TargetCache) -> None:
        """Set the TargetCache for a target"""
        self._repo.set(target.sig(), target_cache.model_dump_json())

    # Public Methods

    def get(
        self,
        target: Target,
        template_path: Path,
        request_args: JSONType | None = None,
    ) -> Response | None:
        """Get a cache entry using the target, the request args and the template path"""
        target_cache = self._get_target_cache(target)
        result = None if target_cache is None else target_cache.get_response(template_path, request_args)
        # Only extract the response
        return result.res if result is not None else None

    def set(
        self,
        target: Target,
        template_path: Path,
        response: Response,
        request_args: JSONType | None = None,
    ) -> None:
        """Set a cache entry using the target, the request args and the template path and the response"""
        # set the response on the target_cache
        target_cache = self._get_target_cache(target) or self._create_target_cache(target)
        # Copy response and set source to 'cache'
        response = deepcopy(response)
        response.source = ResponseSource.CACHE
        # Put response into target cache
        target_cache.set_response(
            template_path,
            request_args,
            CacheResponse(res=response, expiration_time=get_current_time() + self._repo.ttl_seconds),
        )
        # Update the target
        self._set_target_cache(target, target_cache)

    def delete_cache_response(
        self,
        target: Target,
        template_path: Path,
        request_args: JSONType | None = None,
    ) -> None:
        """Clear a cache entry using the target, the request args and the template path"""
        target_cache = self._get_target_cache(target)
        if target_cache:
            target_cache.delete_response(template_path, request_args)

    def delete_cache_subtree(self, target: Target, cache_path: Path) -> None:
        """Delete a cache subtree for the target using the path provided.
        The cache_path can be a template_path or any path
        """
        self.delete_cache_response(target, cache_path)

    def delete_cache_target(self, target: Target) -> None:
        """Clear a cache target using the target"""
        self._repo.delete(target.sig())

    def clear(self) -> None:
        """Clear all the cache"""
        self._repo.clear()
