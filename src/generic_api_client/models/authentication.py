from pydantic import BaseModel


class Credentials(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    token: str
    expiration_time: int | None = None
