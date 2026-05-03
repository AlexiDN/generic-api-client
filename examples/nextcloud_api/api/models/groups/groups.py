from pydantic import BaseModel


class GroupList(BaseModel):
    groups: list[str]
