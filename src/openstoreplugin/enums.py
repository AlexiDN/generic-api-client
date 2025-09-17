from enum import Enum
from pydantic import BaseModel


class TaskStatus(Enum, str):
    SUCCESS = "success"
    FAILURE = "failure"


class TaskResponse(BaseModel):
    status: TaskStatus
    details: str
