from fnmatch import fnmatch
from pathlib import Path
import shutil
from typing import Any, Literal, Self
from pydantic import (
    Field,
    FieldSerializationInfo,
    field_serializer,
    model_validator,
)
from openstoreplugin.models.base_model import BaseConfig
from docker.types.networks import EndpointConfig

# NETWORKS


class IPAMPool(BaseConfig):
    subnet: str = Field(description="Subnet in CIDR format (e.g. '172.28.0.0/16')")
    gateway: str | None = Field(None, description="Gateway address within the subnet")


class IPAMConfig(BaseConfig):
    pool_configs: list[IPAMPool] = Field(description="List of IPAM pools for the network")


class DockerNetworkOptions(BaseConfig):
    name: str = Field(description="Name of the network")
    driver: str | None = Field(None, description="Name of the driver used to create the network")
    internal: bool = Field(False, description="Restrict external access to the network.")
    check_duplicate: bool | None = Field(None, description="Request daemon to check for networks with same name.")
    ipam: IPAMConfig | None = Field(None, description="IPAM configuration for the network")


# CONTAINERS


class DockerVolume(BaseConfig):
    host_path: str = Field(description="Path of the volume on the host")
    container_path: str = Field(description="Path of the volume on the container")
    mode: Literal["ro", "rw"] | None = Field(None, description="Mode of the mount (rw or ro)")
    type: Literal["dir", "file"] | None = Field(None, description="Type of mount (dir or file)")
    removable_globs: list[str] | bool | None = Field(
        None,
        description="The globs of files that are removable during uninstall operation. \
            Can be True to specify that all the volume is deletable. It will be ignored if content is not None",
    )
    content: str | None = Field(None, description="Content of the file if the volume is a file")

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        """Validate coherence of fields"""
        if self.content:
            if not Path(self.host_path).suffix:
                raise ValueError(
                    "Volume can't hold content if the host path does not point to a file (ie has a suffix)"
                )
            if self.type == "dir":
                raise ValueError("Volume can't hold content if its type is directory")
        return self

    def create_on_host(self) -> None:
        """Create the volume on host.
        If there is content -> Create parent directories and file with content
        If there is no content -> Create the volume only if it is a directory (also create parents)
        """
        # if volume is a file with a specified content
        if self.content:
            path = Path(self.host_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.content, encoding="utf-8")
        # if volume is a directory
        elif self.get_type() == "dir":
            Path(self.host_path).mkdir(parents=True, exist_ok=True)

    def remove_from_host(self) -> None:
        """Remove all files and subdirectories of the volumes neccessary depending on self.removable_globs.
        Note: if volume has a content field which is not null it will be removed
        """
        # Full removal (if content->volume is custom file so it should be removed)
        if self.content or self.removable_globs is True:
            # If volume is a file remove it
            if self.get_type() == "file":
                Path(self.host_path).unlink()
            # If volume is a dir delete all the subtree
            else:
                shutil.rmtree(Path(self.host_path))
        # Partial removal
        elif self.removable_globs:
            # If volume is a file remove it if it match a glob
            if self.get_type() == "file" and any(
                fnmatch.fnmatch(self.host_path, pattern) for pattern in self.removable_globs
            ):
                Path(self.host_path).unlink()
            # if volume is a dir
            else:
                for glob in self.removable_globs:
                    # Delete the glob
                    for path in Path(self.host_path).glob(glob):
                        # Dinstinguish directories from files
                        if path.is_file() or path.is_symlink():
                            path.unlink()
                        elif path.is_dir():
                            shutil.rmtree(path)

    def get_type(self) -> Literal["dir", "file"]:
        """Return the type of the volume: either file or dir"""
        if self.type == "file" or self.content or Path(self.host_path).suffix:
            return "file"
        return "dir"

    def to_docker(self) -> str:
        """Convert to a string interpretable by docker"""
        return f"{self.host_path}:{self.container_path}" + (f":{self.mode}" if self.mode else "")


class EndpointConfiguration(BaseConfig):
    ipv4_address: str = Field(description="Custom IPv4 address for the container")
    ipv6_address: str | None = Field(None, description="Custom IPv6 address for the container")

    def to_docker(self, api_version: str) -> EndpointConfig:
        """Convert to EndpointConfig model from docker.types.networks"""
        return EndpointConfig(api_version, **self.model_dump(mode="json", exclude_unset=True))


class RestartPolicy(BaseConfig):
    Name: Literal["on-failure", "always"] = Field(description="The type of policy")
    MaximumRetryCount: int = Field(ge=0, description="Maximum number of retry before stoping the container")


class DockerContainerOptions(BaseConfig, arbitrary_types_allowed=True):
    name: str = Field(description="The name for this container")
    hostname: str = Field(description="Hostname for the container")
    image: str = Field(description="The image to run")
    network: str = Field(description="Name of the network this container will be connected to at creation time")
    networking_config: dict[str, EndpointConfiguration] | None = Field(
        None,
        description="Dictionary of EndpointConfig objects for each container network. \
            The key is the name of the network. Defaults to None.Used in conjuction with network.",
    )
    restart_policy: RestartPolicy | None = Field(None, description="Restart the container when it exits.")
    command: str | list[str] | None = Field(None, description="The command to run in the container")
    entrypoint: str | list[str] | None = Field(None, description="The entrypoint for the container")
    ports: dict[int | str, int | list[int], tuple[str, int]] | None = Field(
        None,
        description="Ports to bind inside the container.\n\
        The keys of the dictionary are the ports to bind inside the container,\
        either as an integer or a string in the form port/protocol, where the protocol is either tcp, udp, or sctp.",
    )
    volumes: list[DockerVolume] = Field(
        [],
        description="A list of volumes mounted inside the container.",
    )
    environment: list[str] | dict[str, str] | None = Field(
        None, description="Environment variables to set inside the container"
    )
    labels: dict[str, str] | list[str] | None = Field(None, description="The labels of the container")
    user: str | int | None = Field(None, description="Username or UID to run commands as inside the container.")
    privileged: bool = Field(False, description="Give extended privileges to this container.")

    @field_serializer("networking_config", when_used="json")
    @staticmethod
    def serialize_networking_config(
        networking_config: dict[str, EndpointConfiguration] | None,
        info: FieldSerializationInfo,
    ) -> EndpointConfig | None:  # Optional[dict[str, EndpointConfiguration]]:
        """Serialize networking_config"""
        if networking_config and isinstance(info.context, dict) and info.context.get("api_version"):
            api_version = info.context.get("docker", "no_version")
            return {key: value.to_docker(api_version) for key, value in networking_config.items()}
        return {key: value.model_dump(**info.__dict__) for key, value in networking_config.items()}

    @field_serializer("volumes", when_used="json")
    @staticmethod
    def serialize_volumes(
        volumes: list[DockerVolume] | None,
        info: FieldSerializationInfo,
    ) -> list[str] | None:
        """Serialize volumes"""
        if volumes and isinstance(info.context, dict) and info.context.get("api_version"):
            return [volume.to_docker() for volume in volumes]
        return [volume.model_dump(**info.__dict__) for volume in volumes]

    def to_docker(self, api_version: str) -> dict[str, Any]:
        """Dump the model to be compatible with docker client.containers.run() command"""
        return self.model_dump(mode="json", exclude_unset=True, context={"api_version": api_version})
