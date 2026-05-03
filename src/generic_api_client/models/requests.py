from http import HTTPMethod, HTTPStatus
from typing import Any
from pydantic import AnyUrl, BaseModel

from generic_api_client.utils import ResponseSource


class Request(BaseModel):
    url: AnyUrl
    method: HTTPMethod
    headers: dict[str, Any]
    params: list[list[str, Any]] | None = None
    data: str | None = None
    body: Any | None = None
    cookies: dict[str, Any] | None = None
    timeout: int = 20
    verify: bool = True

    def update_url_with_uri(self, uri: str) -> None:
        """Update self.url by merging it with uri"""
        self.url = AnyUrl(str(self.url).removesuffix("/") + uri)

    def update_method(self, method: HTTPMethod) -> None:
        """Update self.method"""
        self.method = method

    def update_headers(self, headers: dict[str, Any]) -> None:
        """Update self.headers by merging it with headers"""
        self.headers = headers if self.headers is None else {**self.headers, **headers}

    def update_params(self, params: list[list[str, Any]]) -> None:
        """Update self.params by merging it with params"""
        self.params = params if self.params is None else [*self.params, *params]

    def update_data(self, data: str) -> None:
        """Update self.data"""
        self.data = data

    def update_body(self, json: dict[str, Any]) -> None:
        """Update self.body by merging it with json"""
        self.body = json if self.body is None else {**self.body, **json}

    def update_cookies(self, cookies: dict[str, Any]) -> None:
        """Update self.cookies by merging it with cookies"""
        self.cookies = cookies if self.cookies is None else {**self.cookies, **cookies}


class Response(BaseModel):
    source: ResponseSource = ResponseSource.API
    status_code: HTTPStatus
    headers: dict[str, Any]
    text: str | None = None
    body: Any | None = None
    cookies: dict[str, Any] | None = None
