from collections.abc import Callable
from copy import deepcopy
from functools import wraps
from http import HTTPStatus
from pathlib import Path
from typing import Any, Self, get_args, get_origin, get_type_hints

from pydantic import BaseModel
from semver import Version
from generic_api_client.api_connector_interface import APIConectorInterface
from generic_api_client.exceptions import RequestError
from generic_api_client.models.authentication import Credentials, Token
from generic_api_client.models.requests import Response
from generic_api_client.models.responses import CanonicalModel
from generic_api_client.models.target import Target
from generic_api_client.services.cache_service import CacheService
from generic_api_client.utils import is_instance


class APISegment:
    # Class variables
    # Instance Variables
    connector: APIConectorInterface
    _segment_version: Version | None = None
    _sessions: dict[str, Credentials | Token] | None = None

    @property
    def version(self) -> Version | None:
        """Return the _segment_version if there is one
        otherwise the target version inherited from the parents
        """
        if self._segment_version is None:
            return self.connector.target.version if self.connector.target else None
        return self._segment_version

    # PUBLIC METHODS

    def set_target(self, target: Target, get_version: bool = False) -> None:
        """Set the connector target.
        If get_version is True set _segment_version and target.version
        """
        self.connector.set_target(target)
        if get_version:
            # Extract version and set it for target
            target.version = self.connector.extract_version()
            # Set version for segment
            self._segment_version = target.version
        # Register auth data as main session
        if self._sessions:
            self._sessions["main"] = target.auth_data
        else:
            self._sessions = {"main": target.auth_data}

    def _execute_request(
        self,
        template_path: str,
        request_args: BaseModel | dict[str, Any] | list[BaseModel | dict[str, Any]] | None = None,
        response_processor: Callable[[Self, Response], Response] | None = None,
        allow_private: bool = False,
        login_function: Callable[[Self], Credentials | Token] | None = None,
    ) -> Response:
        """Execute a request base on a template name and request args.
        A response proccessor function can be given to ovveride the connector _proccess_response method.
        If allow_private is False no call to _private/** task can be executed.
        If a login_function is provided and the request fails with a 401 status code
        the login is runned then the request is retried.
        """
        # Normalize path to prevent path traversal
        path = Path(template_path).resolve()
        # Verify private requests
        if not allow_private and "_private" in path.parts:
            msg = f"Can't execute private request {template_path}"
            raise RuntimeError(msg)
        # Override target
        target = self._override_target(deepcopy(self.connector.target))
        # Process request
        try:
            res = self.connector.execute_request(
                template_path,
                request_args,
                response_processor=response_processor,
                target_override=target if target != self.connector.target else None,
            )
        except RequestError as err:
            # If a login func is defined and the error is HTTPStatus.UNAUTHORIZED
            # Login then retry
            if login_function and err.response.status_code == HTTPStatus.UNAUTHORIZED:
                self.connector.target.auth_data = login_function(self)
                res = self.connector.execute_request(
                    template_path,
                    request_args,
                    response_processor=response_processor,
                    target_override=target if target != self.connector.target else None,
                )
            else:
                raise
        return res

    # PRIVATE METHODS

    def __init__(self, connector: APIConectorInterface) -> None:
        self.connector = connector
        self._sessions = {}

    def __init_subclass__(cls) -> type[Self]:
        """Decorate all public methods with 'convert_return_value_decorator'."""
        res = super().__init_subclass__()
        # Iterate through all public methods
        for attr_name in [
            attr
            for attr in dir(cls)
            if not attr.startswith("_") and callable(getattr(cls, attr)) and not isinstance(attr, type)
        ]:
            # decorate the method
            attr = getattr(cls, attr_name)
            setattr(cls, attr_name, cls.convert_return_value_decorator(attr))
        return res

    def _override_target(self, target: Target) -> Target | None:
        """Override the target before executing a request.
        This is useful to ovveride the version of the target or the authentication data (ex:session token).
        """

    @classmethod
    def convert_return_value_decorator(cls, func: Callable) -> Callable:
        """Decorator that converts return values based on type hints."""

        @wraps(func)
        def wrapper(*args: tuple, **kwargs: dict) -> Any:
            # Extract target version from instance
            if args and isinstance(args[0], cls):
                version = args[0].version
            # Execute function
            result = func(*args, **kwargs)
            if isinstance(result, Response):
                # Get type hints for the function
                return_type = get_type_hints(func).get("return", type(None))
                # convert the result if a return_type is found
                if return_type is not type(None):
                    return cls._convert_result(
                        result.body if result.body is not None else result.text,
                        return_type,
                        version,
                    )
            return result

        return wrapper

    @staticmethod
    def _convert_result(  # noqa: C901
        result: object,
        return_type: BaseModel
        | CanonicalModel
        | list[BaseModel | CanonicalModel]
        | dict[Any, BaseModel | CanonicalModel]
        | type,
        version: Version | None = None,
    ) -> Any:
        """Convert a result to the return_type"""
        if is_instance(result, return_type):
            return result
        origin = get_origin(return_type)
        args = get_args(return_type)
        if origin is list:
            if len(args) != 1:
                msg = f"Invalid args {args}."
                raise RuntimeError(msg)
            if not isinstance(result, list):
                msg = f"Can't convert result of type {type(result)} to {return_type}"
                raise RuntimeError(msg)
            inner_type = args[0]
            return [APISegment._convert_result(item, inner_type) for item in result] if result else []
        if origin is dict:
            if len(args) != 2:  # noqa: PLR2004
                msg = f"Invalid args {args}."
                raise RuntimeError(msg)
            if not isinstance(result, dict):
                msg = f"Can't convert result of type {type(result)} to {return_type}"
                raise RuntimeError(msg)
            key_type, val_type = args
            return (
                {
                    APISegment._convert_result(k, key_type): APISegment._convert_result(v, val_type)
                    for k, v in result.items()
                }
                if result
                else {}
            )

        # Pydantic model case
        if issubclass(return_type, BaseModel):
            # Ensure that the result is a dict before creating the model
            if isinstance(result, dict):
                # CanonicalModel model case
                if issubclass(return_type, CanonicalModel):
                    return return_type.from_version(result, version)
                return return_type.model_validate(result)
            msg = f"Can't convert result of type {type(result)} to model {return_type.__name__}"
            raise TypeError(msg)
        # Non Pydantic model case
        return return_type(result)


class APIAggregate(APISegment):
    """A base class to declare a aggregate of api segments.</br>
    The subclass implementation MUST redefined the field 'connector' with the custom APIConectorInterface as type hint.
    """

    def __init__(
        self,
        connector: APIConectorInterface | None = None,
        cache_service: CacheService | None = None,
    ) -> None:
        # init connector is not given create it from hints
        if not connector:
            connector_type: APIConectorInterface = get_type_hints(self.__class__, include_extras=True).get(
                "connector", APIConectorInterface
            )
            if connector_type == APIConectorInterface:
                msg = f"Can't create {self.__class__} because field 'connector' is not typed properly."
                raise RuntimeError(msg)
            if cache_service is None:
                msg = f"Can't create {self.__class__} because no cache_service were provided"
                raise ValueError(msg)
            self.connector = connector_type(cache_service)
        else:
            self.connector = connector
        # init all segments and aggregate
        attrs = {k: v for k, v in get_type_hints(self, include_extras=True).items() if issubclass(v, APISegment)}
        for attr_name, attr_type in attrs.items():
            if not issubclass(attr_type, (APIAggregate, APISegment)):
                msg = f"{attr_name} of {self.__class__} is not a subclass of APIAggregate or APISegment."
                raise TypeError(msg)
            # init the attribute
            setattr(self, attr_name, attr_type(self.connector))

    def recursive_call(self, method_name: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        """Call a method on all subsegments|subaggregates recursively"""
        subs = [k for k, v in get_type_hints(self, include_extras=True).items() if hasattr(v, method_name)]
        for sub_name in subs:
            sub = getattr(self, sub_name)
            method = getattr(sub, method_name)
            method(*args, **kwargs)
