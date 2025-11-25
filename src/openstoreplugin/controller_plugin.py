from typing import Any

from openstoreplugin.controller_tasks_args import CONTROLLER_DEFAULT_TASKS
from openstoreplugin.models.controller_task import ControllerTask

from openstoreplugin.models.store_config import OpenStoreConfigModel
from openstoreplugin.models.application_config import ApplicationConfiguration
from openstoreplugin.enums import TaskResponse, TaskStatus
from openstoreplugin.connectors import DockerEngineConnector


class ControllerPlugin:
    application_config: ApplicationConfiguration
    docker_connector: DockerEngineConnector
    tasks: dict[str, ControllerTask]
    store_config: OpenStoreConfigModel

    def __init__(
        self,
        application_config: ApplicationConfiguration,
        store_config: OpenStoreConfigModel,
    ) -> None:
        self.application_config = application_config
        self.application_config.set_store_config(store_config)
        self.docker_connector = DockerEngineConnector()
        self.store_config = store_config
        # create task mapping after verifying method exist
        # TODO also verify args and make it better to declaire tasks using decorator @tasks to prefill arg of __init__
        for task in CONTROLLER_DEFAULT_TASKS:
            if not hasattr(self, task.controller_method.name):
                msg = f"{self.__class__.__name__} does not have method \
                    {task.controller_method.name} required for task {task.name}"
                raise ValueError(msg)
        self.tasks = {task.name: task for task in CONTROLLER_DEFAULT_TASKS}

    def execute_task(self, task: str, **kwargs: dict[str, Any]) -> TaskResponse:
        """Execute a task using the tasks mapping of the instance.
        Return the TaskResponse return by the method called
        """
        # verify task exist
        if task in self.tasks:
            method_info = self.tasks.get(task).controller_method
            method_args = {arg.name: arg for arg in method_info.args}
            # verify task arguments
            for arg, value in kwargs.items():
                if arg not in method_args or not isinstance(value, method_args[arg].type_):
                    msg = f"Arg {arg} does not match any arguments avalaible for task {task}.\
                        Available args: {method_args.keys()}"
                    raise ValueError(msg)
            # extract method
            method = getattr(self, method_info.name)
            try:
                return method(**kwargs) or TaskResponse(status=TaskStatus.SUCCESS)
            except Exception as err:
                return TaskResponse(
                    status=TaskStatus.FAILURE,
                    details=f"{err.__class__.__name__}:{err}",
                )
        msg = f"Task {task} does not exist."
        raise RuntimeError(msg)

    # ================
    # Default tasks
    # ================

    def install(self) -> None:
        """Install the application"""
        self.create_bind_mounts()
        self.deploy_docker()
        return TaskResponse(status=TaskStatus.SUCCESS)

    def create_bind_mounts(self) -> None:
        """Create the directories and files mounted onto the docker container"""
        for docker_config in self.application_config.docker_configs:
            for volume in docker_config.container_options.volumes:
                volume.create_on_host()

    def delete_bind_mounts(self) -> None:
        """Delete all bind mounts for the application"""
        for docker_config in self.application_config.docker_configs:
            for volume in docker_config.container_options.volumes:
                volume.remove_from_host()

    def deploy_docker(self) -> None:
        """Deploy the docker part of the application"""
        docker_configs = self.application_config.docker_configs
        for docker_config in docker_configs:
            # create network if it does not exist
            if not self.docker_connector.get_network_from_name(
                docker_config.container_options.network,
                allow_failure=True,
            ):
                if not hasattr(docker_config, "network_options"):
                    msg = f"Network {docker_config.container_options.network} \
                        does not exist and is not declared in application config"
                    raise ValueError(msg)
                self.docker_connector.create_network(docker_config.network_options)

            # deploy the container
            self.docker_connector.deploy_container(docker_config.container_options)

    def uninstall(self, cleanup_volumes: bool = False) -> None:
        """Uninstall the application"""
        # remove docker containers
        for docker_config in self.application_config.docker_configs:
            self.docker_connector.remove_container(docker_config.container_options.name)
        # cleanup volumes
        if cleanup_volumes:
            self.delete_bind_mounts()
