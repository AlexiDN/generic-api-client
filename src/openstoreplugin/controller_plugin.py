from jinja2 import Template

from .application_config import ApplicationConfiguration
from .enums import TaskResponse


class ControllerPlugin:
    application_config: ApplicationConfiguration
    application_docker_template: Template
    task_mapping: dict[str, callable]

    def __init__(self, application_config: ApplicationConfiguration, application_docker_template: Template) -> None:
        self.application_config = application_config
        self.application_docker_template = application_docker_template

    def execute_task(self, task: str) -> TaskResponse:
        """Execute a task using the task_mapping of the instance.
        Return the TaskResponse return by the method called
        """
        method = self.task_mapping.get(task)
        if method:
            return method()
        msg = f"Task {task} does not exist."
        raise RuntimeError(msg)
