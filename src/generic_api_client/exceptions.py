from generic_api_client.models.requests import Response


class RequestError(Exception):
    message: str
    response: Response

    def __init__(self, response: Response, message: str) -> None:
        super().__init__(message)
        self.message = message
        self.response = response

    def __str__(self) -> str:  # noqa: D105
        return self.message + f"\nResponse: {self.response}"
