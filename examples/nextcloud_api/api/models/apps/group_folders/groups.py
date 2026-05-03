from typing import Literal
from pydantic import BaseModel


class Group(BaseModel):
    gid: str
    displayName: str


class GroupDetails(BaseModel):
    displayName: str
    permissions: int
    type: Literal["group", "circle"]
