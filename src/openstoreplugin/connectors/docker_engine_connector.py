from docker import from_env
from docker.errors import NotFound
from docker.models.containers import Container, ExecResult
from docker.models.networks import Network

from openstoreplugin.models.docker import DockerContainerOptions, DockerNetworkOptions


class DockerEngineConnector:
    user: str

    def __init__(self, user: str = "root") -> None:
        self.client = from_env()
        self.user = user

    def get_api_version(self) -> str:
        """Return the docker API Version or 'Unknown' if it does not exist"""
        return self.client.version().get("ApiVersion", "Unknown")

    def get_container_from_hostname(self, container_hostname: str, allow_failure: bool = False) -> Container:
        """Return the container associated to the hostname given or raise an error if it is not found"""
        for container in self.client.containers.list():
            hostname = container.attrs.get("Config", {})("Hostname")
            if hostname == container_hostname:
                return container
        if allow_failure:
            return None
        msg = f"No container found with hostname {container_hostname}."
        raise NotFound(msg)

    def get_container_from_name(self, container_name: str, allow_failure: bool = False) -> Container:
        """Return the container associated to the name given or raise an error if it is not found"""
        try:
            return self.client.containers.get(container_name)
        except NotFound as err:
            if allow_failure:
                return None
            msg = f"No container found with name {container_name}."
            raise NotFound(msg) from err

    def get_network_from_name(self, network_name: str, allow_failure: bool = False) -> Network:
        """Return the network associated to the name given or raise an error if it is not found"""
        try:
            return self.client.networks.get(network_name)
        except NotFound as err:
            if allow_failure:
                return None
            msg = f"No network found with name {network_name}."
            raise NotFound(msg) from err

    def execute_command_on_container(self, container_name: str, command: str, user: str | None = None) -> ExecResult:
        """Execute the command on the container described
        by container_name and return the ExecResult object associated
        """
        return self.get_container_from_name(container_name).exec_run(command, user=user or self.user)

    def deploy_container(self, options: DockerContainerOptions) -> str:
        """Deploy a container and return its name"""
        try:
            self.get_network_from_name(options.network)
        except NotFound as err:
            msg = f"Can't deploy container {options.name} since the network {options.network} does not exist."
            raise RuntimeError(msg) from err
        data = options.to_docker(self.get_api_version())
        container: Container = self.client.containers.run(detach=True, **data)
        return container.name

    def remove_container(self, container_name: str, force: bool = True) -> None:
        """Remove a container from docker"""
        if force:
            self.stop_container(container_name)
        return self.get_container_from_name(container_name).remove()

    def start_container(self, container_name: str) -> None:
        """Start an already created container"""
        return self.get_container_from_name(container_name).start()

    def stop_container(self, container_name: str, timeout: int = 60) -> None:
        """Stop the container without removing it"""
        return self.get_container_from_name(container_name).stop(timeout=timeout)

    def create_network(self, network_options: DockerNetworkOptions) -> str:
        """Create a docker network"""
        return self.client.networks.create(**network_options.model_dump(mode="json", exclude_unset=True)).name

    def remove_network(self, network_name: str) -> None:
        """Remove a Docker network and return its name"""
        return self.get_network_from_name(network_name).remove()
