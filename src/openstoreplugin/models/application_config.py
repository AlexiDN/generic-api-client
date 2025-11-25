from typing import Any
from pydantic import Field

from openstoreplugin.models.base_model import BaseConfig

from openstoreplugin.models.docker import DockerContainerOptions, DockerNetworkOptions


class DockerConfig(BaseConfig):
    container_options: DockerContainerOptions = Field(title="Options for the docker container")
    network_options: DockerNetworkOptions | None = Field(
        None, title="Options for the docker network used by the container if it does not already exist "
    )


class ApplicationConfiguration(BaseConfig):
    version: str = Field(title="Version of the Application")
    docker_configs: list[DockerConfig] = Field(title="Options for the docker containers")
    extra: dict[str, Any] = Field(default={}, title="Extra configuration")
