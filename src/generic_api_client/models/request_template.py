from http import HTTPMethod
from typing import Any
from pydantic import BaseModel, Field
from semver import Version

from generic_api_client.utils import check_constraint


class RequestOptions(BaseModel):
    endpoint: str = Field("", description="The endpoint path")
    method: HTTPMethod | None = None
    headers: dict[str, Any] | None = None
    params: list[list[str, Any]] | None = None
    cookies: dict[str, Any] | None = None
    body: dict | str | None = None


class RequestTemplate(BaseModel):
    requires_auth: bool = Field(True, description="Either the request requires authentication or not.")
    requires_version: bool = Field(False, description="Either the request requires API version or not.")
    general_options: RequestOptions | None = Field(description="Options which are common to all versions of the API.")
    version_options: dict[str, RequestOptions] = Field(
        description="Options that depends on some API versions.", default_factory=dict
    )

    def get_final_request_options(self, api_version: Version | None = None) -> RequestOptions:
        """Get the request options from the template using the api_version."""
        # Get general options
        request_options = (
            self.general_options.model_dump(mode="json", exclude_unset=True, exclude_none=True)
            if self.general_options
            else {}
        )
        # Get version options
        if api_version:
            for constraint, options in self.version_options.items():
                if check_constraint(api_version, constraint):
                    request_options.update(options.model_dump(mode="json", exclude_unset=True, exclude_none=True))
                    break

        return RequestOptions.model_validate(request_options)
