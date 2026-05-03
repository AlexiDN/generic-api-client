import hashlib
from pydantic import BaseModel

from generic_api_client.utils import get_current_time


class Credentials(BaseModel):
    username: str
    password: str

    def sig(self) -> str:
        """Return the signature of the credentials."""
        return f"{self.username}/{hashlib.sha256(self.password.encode()).hexdigest()}"


class Token(BaseModel):
    token: str
    expiration_time: int | float | None = None

    def sig(self) -> str:
        """Return the signature of the token."""
        return hashlib.sha256(self.token.encode()).hexdigest()

    def is_valid(self) -> bool:
        """Return either the token is valid"""
        if self.expiration_time is None:
            return True
        return get_current_time() < self.expiration_time
