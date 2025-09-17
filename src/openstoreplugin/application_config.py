from typing import Any
from pydantic import BaseModel, Field


class MountedFileConfiguration(BaseModel):
    content: str = Field(title="Contend of the file")
    host_path: str = Field(title="Path of the file outside the container")
    container_path: str = Field(title="Path of the file inside the container")


class DockerComposeArgs(BaseModel):
    traefik_labels: list[str] = Field(default=[], title="Labels for Traefik")
    mounted_files: dict[str, MountedFileConfiguration] = Field(
        default={}, title="Configurations for files mounted onto the container"
    )
    extra: dict[str, Any] = Field(default={}, title="Extra Arguments")


class ApplicationConfiguration(BaseModel):
    version: str = Field(title="Version of the Application")
    docker_compose_args: DockerComposeArgs = Field(title="Arguments for docker compose")
    extra: dict[str, Any] = Field(default={}, title="Extra configuration")
