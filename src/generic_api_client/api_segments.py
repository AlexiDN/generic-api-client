from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Self, get_args, get_origin, get_type_hints

from pydantic import BaseModel
from generic_api_client.api_connector_interface import APIConectorInterface
from generic_api_client.models.requests import Response
from generic_api_client.models.target import Target


@dataclass
class APISegment:
    connector: APIConectorInterface

    def __init_subclass__(cls) -> type[Self]:
        """Decorate all public methods with 'convert_return_value_decorator'."""
        res = super().__init_subclass__()
        # Iterate through all attributes
        for attr_name in [
            attr
            for attr in dir(cls)
            if not attr.startswith("_") and callable(getattr(cls, attr)) and not isinstance(attr, type)
        ]:
            attr = getattr(cls, attr_name)
            setattr(cls, attr_name, APISegment.convert_return_value_decorator(attr))
        return res

    @staticmethod
    def convert_return_value_decorator(func: Callable) -> Callable:
        """Decorator that converts return values based on type hints."""

        @wraps(func)
        def wrapper(*args: tuple, **kwargs: dict) -> Any:
            # Execute function
            result = func(*args, **kwargs)
            if isinstance(result, Response):
                # Get type hints for the function
                return_type = get_type_hints(func).get("return", None)
                # convert the result if a return_type is found
                if return_type is not None:
                    return APISegment._convert_result(result.json or result.text, return_type)
            return result

        return wrapper

    @staticmethod
    def _convert_result(result: object, return_type: BaseModel | list[BaseModel] | type) -> Any:
        """Convert a result to the return_type"""
        origin = get_origin(return_type)
        if origin is list:
            # Get the type inside list[...]
            args = get_args(return_type)
            if len(args) != 1:
                msg = f"Invalid args {args}."
                raise RuntimeError(msg)
            if not isinstance(result, list):
                msg = f"Can't convert result of type {type(result)} to {return_type}"
                raise RuntimeError(msg)
            inner_type = args[0]
            return [APISegment._convert_result(item, inner_type) for item in result]

        # Pydantic model case
        if issubclass(return_type, BaseModel):
            # Ensure that the result is a dict before creating the model
            if isinstance(result, dict):
                return return_type.model_validate(result)
            msg = f"Can't convert result of type {type(result)} to model {return_type.__name__}"
            raise TypeError(msg)
        # Non Pydantic model case
        return return_type(result)


class APIAggregate(APISegment):
    """A base class to declare a aggregate of api segments.</br>
    The subclass implementation MUST redefined the field 'connector' with the custom APIConectorInterface as type hint.
    """

    def __init__(self, connector: APIConectorInterface | None = None) -> None:
        # init connector is not given create it from hints
        if not connector:
            connector_type: APIConectorInterface = get_type_hints(self.__class__, include_extras=True).get(
                "connector", APIConectorInterface
            )
            if connector_type == APIConectorInterface:
                msg = f"Can't create {self.__class__} because field 'connector' is not typed properly."
                raise RuntimeError(msg)
            connector = connector_type()
        # init parent
        super().__init__(connector)
        attrs = {
            k: v
            for k, v in get_type_hints(self, include_extras=True).items()
            if k not in get_type_hints(APISegment, include_extras=True)
        }
        # init all segments and aggregate
        for attr_name, attr_type in attrs.items():
            if not issubclass(attr_type, (APIAggregate, APISegment)):
                msg = f"{attr_name} of {self.__class__} is not a subclass of APIAggregate or APISegment."
                raise TypeError(msg)
            # init the attribute
            setattr(self, attr_name, attr_type(self.connector))

    def set_target(self, target: Target) -> None:
        """Set the connector target"""
        self.connector.set_target(target)
