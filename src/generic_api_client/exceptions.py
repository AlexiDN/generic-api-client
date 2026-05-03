from semver import Version

from generic_api_client.models.requests import Response, Request


class RequestError(Exception):
    message: str
    response: Response
    request: Request | None

    def __init__(self, message: str, response: Response, request: Request | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.response = response
        self.request = request

    def __str__(self) -> str:  # noqa: D105
        return self.message + (f"\nRequest: {self.request}" if self.request else "") + f"\nResponse: {self.response}"


class UnsupportedVersionError(Exception):
    message: str
    version: Version

    def __init__(self, version: Version, message: str | None, justification: str | None = None) -> None:
        super().__init__(message)
        self.version = version
        self.message = (message or f"Unsupported version:{version}.") + (f"\n{justification}" if justification else "")

    def __str__(self) -> str:  # noqa: D105
        return self.message
