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

    def clear_empty_params(self) -> None:
        """Clear any empty param"""
        if self.params:
            self.params = [
                param
                for param in self.params
                if len(param) == 2 and param[1] != "None" and param[1] is not None  # noqa: PLR2004
            ]

    def clear_empty_headers(self) -> None:
        """Clear any empty header"""
        if self.headers:
            for k, value in self.headers.items():
                if value is None or value == "None":
                    self.headers.pop(k)

    def clear_empty_cookies(self) -> None:
        """Clear any empty cookie"""
        if self.cookies:
            for k, value in self.cookies.items():
                if value is None or value == "None":
                    self.cookies.pop(k)

    def clear_empty_basic_body_strings(self) -> None:
        """Clear empty strings of the body. Does not recurse on nested values"""
        if self.body and isinstance(self.body, dict):
            for k, value in self.body.items():
                if value is None or value == "None":
                    self.body.pop(k)
        # If body is str and empty delete it
        if isinstance(self.body, str) and self.body == "None":
            self.body = None


class RequestTemplate(BaseModel):
    requires_auth: bool = Field(True, description="Either the request requires authentication or not.")
    requires_version: bool = Field(False, description="Either the request requires API version or not.")
    general_options: RequestOptions | None = Field(description="Options which are common to all versions of the API.")
    version_options: dict[str, RequestOptions] = Field(
        description="Options that depends on some API versions.", default_factory=dict
    )
    write_action: bool = Field(
        default=False,
        description=(
            "Whether the request is a write action on the target."
            " This determines if the request should erase the cache subtree"
        ),
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

        request_options = RequestOptions.model_validate(request_options)
        request_options.clear_empty_basic_body_strings()
        request_options.clear_empty_cookies()
        request_options.clear_empty_headers()
        request_options.clear_empty_params()
        return request_options
