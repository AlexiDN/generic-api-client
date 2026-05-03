from examples.nextcloud_api.api.models.groups.groups import GroupList
from examples.nextcloud_api.api.segments.interfaces import NextCloudAPIBaseAggregate


class NextCloudGroups(NextCloudAPIBaseAggregate):
    def list_groups(
        self,
        search_query: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> GroupList:
        """List all the groups"""
        return self._execute_request(
            "ocs/v2_php/cloud/groups/list", {"SEARCH": search_query, "LIMIT": limit, "OFFSET": offset}
        )
