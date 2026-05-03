from typing import Literal
from pydantic import BaseModel


class AclManage(BaseModel):
    displayname: str
    id: str
    type: Literal["user", "group", "circle"]


class GroupDetails(BaseModel):
    displayName: str
    permissions: int
    type: Literal["group", "circle"]


class GroupFolder(BaseModel):
    id: int
    mount_point: str
    quota: int
    acl: bool
    size: int
    groups: dict[str, int] | list
    group_details: dict[str, GroupDetails] | list
    manage: list[AclManage] | list

    def include_group(self, group_name: str) -> bool:
        """Return either the group is allowed for the GroupFolder"""
        if not self.groups:
            return False
        return group_name in self.groups


class GrantAccessToFolderResponse(BaseModel):
    success: bool
    folder: GroupFolder
