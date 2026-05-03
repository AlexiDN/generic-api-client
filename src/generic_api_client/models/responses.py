from copy import deepcopy
import re
from typing import ClassVar, Self

from pydantic import BaseModel, ValidationError
from semver import Version

from generic_api_client.exceptions import UnsupportedVersionError


class VersionnedModel(BaseModel):
    """Base Class for a versionned model"""

    __version__: ClassVar[Version]

    @classmethod
    def version(cls) -> Version:
        """Return cls.__version__"""
        return cls.__version__

    def __init_subclass__(cls) -> None:
        """Setup class attribute version from class name if it is not set yet"""
        if not isinstance(getattr(cls, "__version__", None), Version):
            cls.__version__ = cls.extract_version_from_class_name(cls.__name__)

    @staticmethod
    def extract_version_from_class_name(name: str) -> Version:
        """Extract a semver version from a class name"""
        pattern = (
            r"(\d+)_(\d+)_(\d+)"  # major_minor_patch
            r"(?:_(alpha|beta|rc)"  # optional prerelease tag
            r"_?(\d+)?)?"  # optional prerelease number
        )

        match = re.search(pattern, name, re.IGNORECASE)
        if not match:
            msg = f"No semver version found in class name: {name}"
            raise ValueError(msg)

        major, minor, patch, pre_tag, pre_num = match.groups()

        version = f"{major}.{minor}.{patch}"

        if pre_tag:
            # Normalize prerelease to semver style
            pre_tag = pre_tag.lower()
            pre_num = pre_num or "0"
            version += f"-{pre_tag}.{pre_num}"

        return Version.parse(version)


class CanonicalModel(BaseModel):
    """Base Class for the canonical version of a model"""

    # Class attributes
    _versionned_models: ClassVar[list[VersionnedModel]]

    @classmethod
    def from_version(cls, data: dict | VersionnedModel, origin: Version | None = None) -> Self:
        """Build a CanonicalModel from raw data or a VersionnedModel"""
        model = data if isinstance(data, VersionnedModel) else None
        # Parse data to a matching VersionnedModel if required
        if isinstance(data, dict):
            # If origin is specified parse data
            if origin:
                model = cls.get_versionned_model(origin).model_validate(data, by_alias=True)
            # Otherwise try every model from last to older
            else:
                available_models = deepcopy(cls._versionned_models)
                available_models.sort(key=lambda model: model.version(), reverse=True)
                for model_class in cls._versionned_models:
                    try:
                        model = model_class.model_validate(data, by_alias=True)
                        continue
                    except ValidationError:
                        pass
        # verify that model is set
        if not model:
            msg = (
                f"Can't create {cls.__name__} because data does not match any"
                f" versionned models:{[model.__name__ for model in cls._versionned_models]}"
            )
            raise RuntimeError(msg)
        return cls.model_validate(model.model_dump(mode="json", by_alias=False), by_name=True)

    def to_version(self, version: Version) -> VersionnedModel:
        """Convert the current model to a specific version."""
        model_class = self.get_versionned_model(version)
        return model_class.model_validate(self.model_dump(mode="json", by_alias=False), by_name=True)

    @classmethod
    def get_versionned_model(cls, version: Version) -> type[VersionnedModel]:
        """Return the versionned model variant that satisfies the version if it exist."""
        versionned_models = {model.version(): model for model in cls._versionned_models}

        # If there is a variant for that specific variant return it
        if version in versionned_models:
            return versionned_models[version]

        versions = [*list(versionned_models), version]
        versions.sort()
        # Check that the version is not too old
        if versions[0] == version:
            raise UnsupportedVersionError(
                version,
                justification=(
                    f"Can't find any {cls.__name__} variant which satisfies this version because it is too old."
                ),
            )
        # Return nearest older supported version
        return versions[versions.index(version) - 1]
