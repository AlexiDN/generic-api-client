from pydantic import BaseModel
from semver import Version

from generic_api_client.models.responses import CanonicalModel, VersionnedModel


class NextCloudAppsListBase(BaseModel):
    apps: list[str]


class NextCloudAppsList_1(VersionnedModel, NextCloudAppsListBase):
    __version__ = Version(32)


class NextCloudAppsList_2(VersionnedModel, NextCloudAppsListBase):
    __version__ = Version(10)


class NextCloudAppsList(CanonicalModel, NextCloudAppsListBase):
    _versionned_models = [NextCloudAppsList_1, NextCloudAppsList_2]
