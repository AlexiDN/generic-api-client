from pydantic import AnyUrl, BaseModel, field_serializer, field_validator
from semver import Version

from generic_api_client.models.authentication import Credentials, Token


class Target(BaseModel, arbitrary_types_allowed=True):
    url: AnyUrl
    auth_data: Credentials | Token | None = None
    version: Version | None = None

    @field_serializer("version", when_used="json-unless-none")
    @staticmethod
    def serialize_version(version: Version) -> str:
        """Serialize version to str"""
        return str(version)

    @field_validator("version", mode="before")
    @staticmethod
    def parse_version(version: str | None) -> Version | None:
        """Parse version from str"""
        if version:
            return Version.parse(version)
        return None

    def sig(self) -> str:
        """Return the signature of the target.
        The signature is calculated using all the fields of the target.
        """
        url_sig = str(self.url).removesuffix("/").removeprefix("https://").removeprefix("http")
        auth_sig = self.auth_data.sig() if self.auth_data is not None else ""
        version_sig = str(self.version) if self.version else ""
        return f"{url_sig}:{auth_sig}:{version_sig}"
