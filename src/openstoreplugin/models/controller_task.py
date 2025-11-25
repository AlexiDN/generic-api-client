from pydantic import BaseModel, Field


class MethodArg(BaseModel):
    name: str = Field(description="Name of the arg. ex: 'timeout'.")
    type_: type = Field(description="Type of the arg. ex: int.", alias="type")
    description: str = Field(description="Description of the arg. ex: 'Timeout of the action'.")


class ControllerMethod(BaseModel):
    name: str = Field(description="Name of the method. ex: 'install'.")
    args: list[MethodArg] = Field([], description="List of the args of the method.")


class ControllerTask(BaseModel):
    name: str = Field(description="Name of the task. ex: 'Install'.")
    description: str = Field(description="Description of the task. ex: 'Install the app'.")
    controller_method: ControllerMethod = Field(description="Controller Method associated.")
