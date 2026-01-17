from pydantic import AnyUrl, BaseModel

from generic_api_client.models.authentication import Credentials, Token


class Target(BaseModel):
    url: AnyUrl
    auth_data: Credentials | Token | None = None

    def sig(self) -> str:
        """Return the signature of the target.
        The signature is calculated using the url of the target.
        """
        return str(self.url).removesuffix("/").removeprefix("https://").removeprefix("http")
