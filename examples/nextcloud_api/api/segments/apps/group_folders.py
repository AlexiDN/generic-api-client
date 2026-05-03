from generic_api_client import APISegment

from examples.nextcloud_api.api.models.apps.group_folders.folders import GrantAccessToFolderResponse, GroupFolder
from examples.nextcloud_api.api.models.apps.group_folders.groups import Group


class NextCloudAppGroupFolders(APISegment):
    def list_group_folders(self) -> dict[str, GroupFolder]:
        """List all the groups folders"""
        res = self._execute_request("index_php/apps/groupfolders/folders/list")
        # Maintain type consistance instead of empty list
        res.body = res.body or {}
        return res

    def list_groups(self) -> list[Group]:
        """List all the groups"""
        return self._execute_request("index_php/apps/groupfolders/delegation/groups/list")

    def create_group_folder(self, folder_name: str) -> GroupFolder:
        """Create a group folder"""
        return self._execute_request(
            "index_php/apps/groupfolders/folders/create_new_folder", {"FOLDER_NAME": folder_name}
        )

    def grant_access_to_group_folder(self, folder_id: int, group_name: str) -> GrantAccessToFolderResponse:
        """Grant access to the folder for a specific group"""
        return self._execute_request(
            "index_php/apps/groupfolders/folders/add_access_for_group",
            {"FOLDER_ID": folder_id, "GROUP_NAME": group_name},
        )
