from openstoreplugin.models.controller_task import ControllerMethod, ControllerTask, MethodArg


CONTROLLER_DEFAULT_TASKS = [
    ControllerTask(
        name="Install",
        description="Install the application.",
        controller_method=ControllerMethod(
            name="install",
        ),
    ),
    ControllerTask(
        name="Uninstall",
        description="Uninstall the application and optionnally remove its files.",
        controller_method=ControllerMethod(
            name="uninstall",
            args=[
                MethodArg(
                    name="cleanup_volumes",
                    type=bool,
                    description="Should the applications files be removed?",
                )
            ],
        ),
    ),
]
