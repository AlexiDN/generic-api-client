from http import HTTPMethod
from typing import Any

from pydantic import BaseModel, Field


class RetryConfig(BaseModel):
    delay: float | int = Field(1, description="Initial retry delay in seconds")
    backoff: float | int = Field(1, description="Multiplier for the retry delay")
    max_retries: int = Field(0, description="The number of retries allowed for a request")

    def update_delay(self) -> None:
        """Update delay after one retry"""
        self.delay *= self.backoff


class APICommonRequestFields(BaseModel):
    """API common requests fields"""

    root_url: str = Field("", description="The api root url", examples=["ocs/v2.php/cloud"])
    method: HTTPMethod | None = Field(None, description="Default method for API requests")
    headers: dict[str, Any] | None = Field(None, description="Default headers for API requests")
    cookies: dict[str, Any] | None = Field(None, description="Default cookies for API requests")
    data: str | None = Field(None, description="Default data for API requests")
    body: Any | None = Field(None, description="Default json for API requests")
    requires_login: bool = Field(False, description="Either the API requires a login")
    requires_version: bool = Field(False, description="Either the API requires to know the target version")
    timeout: int = Field(20, description="The API requests timeout in seconds")
    verify: bool = Field(True, description="Either to use https(True) or http(False)")
    retries: RetryConfig = Field(description="The configuration to retry a request", default_factory=RetryConfig)
