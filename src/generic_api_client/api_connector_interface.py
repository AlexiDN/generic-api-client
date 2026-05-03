# ruff: noqa: ARG002
from contextvars import Token
from http import HTTPMethod, HTTPStatus
from pathlib import Path
from time import sleep
from typing import Any, ClassVar, Self
from collections.abc import Callable
from pydantic import BaseModel
from requests import Response as RequestsResponse, request as requests_request

from generic_api_client.exceptions import RequestError
from generic_api_client.models.request_template import RequestTemplate
from generic_api_client.services.cache_service import CacheService
from generic_api_client.utils import to_json
from .models.authentication import Credentials
from .models.requests import Request, Response
from .models.api import APICommonRequestFields
from semver import Version

from .models.target import Target
from .services.template_service import TemplateService


class APIConectorInterface:
    # Class fields
    no_retries_on_status: ClassVar[list[HTTPStatus]] = [HTTPStatus.UNAUTHORIZED]
    api_common_requests_fields: ClassVar[APICommonRequestFields] = None
    templates_dir: Path = None
    template_service: TemplateService
    cache_service: CacheService
    # Instance fields
    # Field initialized by login method
    api_auth_data: Credentials | Token | None = None
    # Field definining on which target to execute the api
    _permanent_target: Target | None = None
    # Request specific memory
    _current_target: Target | None = None
    _current_request: Request | None = None

    @property
    def target(self) -> Target | None:
        """Target property of the connector to use for request methods."""
        return self._current_target or self._permanent_target

    # CONSTRUCTOR
    def __new__(cls, *_args: tuple, **_kwargs: dict) -> Self:
        """Verify that the class implementation is correct before building an instance."""
        if not hasattr(cls, "api_common_requests_fields"):
            msg = f"Can't instantiate {cls} because api_common_requests_fields field needs to be defined."
            raise RuntimeError(msg)
        if not hasattr(cls, "templates_dir"):
            msg = f"Can't instantiate {cls} because templates_dir field needs to be defined."
            raise RuntimeError(msg)
        cls.template_service = TemplateService(Path(cls.templates_dir))
        return super().__new__(cls)

    def __init__(self, cache_service: CacheService) -> None:
        self.cache_service = cache_service

    # PUBLIC METHODS

    def set_target(self, target: Target) -> None:
        """Set self._permanent_target"""
        self._permanent_target = target

    def get_target(self) -> Target | None:
        """Return self._permanent_target"""
        return self._permanent_target

    def login(self) -> None:
        """Authenticate to the API"""
        try:
            # execute login
            res = self.execute_request("_private/login")
            # set api_auth_data from response
            self._extract_auth_from_response(res)
        except FileNotFoundError as err:
            msg = f"Can't execute required login because the task where not found. Exc:{err}"
            raise RuntimeError(msg) from err

    def extract_version(self) -> Version:
        """Retrieve of the API version"""
        try:
            # execute get_version
            res = self.execute_request("_private/version")
            # set version from response
            version = self._extract_version_from_response(res)
        except FileNotFoundError as err:
            msg = f"Can't execute required 'load_version' because the task where not found. Exc:{err}"
            raise RuntimeError(msg) from err
        else:
            self.target.version = version
            return version

    def execute_request(
        self,
        template_path: str,
        request_args: BaseModel | dict[str, Any] | list[BaseModel | dict[str, Any]] | None = None,
        target_override: Target | None = None,
        response_processor: Callable[[Self, Response], Response] | None = None,
        use_cache: bool = True,
    ) -> Response:
        """Execute a request base on a template name and request args.
        A response proccessor function can be given to ovveride the instance _proccess_response.
        A target_ovver
        """
        self._current_target = target_override

        if use_cache:
            cache_response = self.cache_service.get(
                target=self.target,
                template_path=Path(template_path),
                request_args=to_json(request_args),
            )
            # If there is a cache hit return it
            if cache_response:
                return cache_response
        try:
            # Verify that the target was defined before
            if not self.target:
                msg = (
                    f"Can't execute the request {template_path} since not "
                    "target was defined. Use 'set_target' before executing a request."
                )
                raise RuntimeError(msg)
            # Prepare request general fields
            prepared_request = Request(
                url=str(self.target.url) + self.api_common_requests_fields.root_url,
                method=self.api_common_requests_fields.method or HTTPMethod.CONNECT,
                headers=self.api_common_requests_fields.headers,
                cookies=self.api_common_requests_fields.cookies,
                timeout=self.api_common_requests_fields.timeout,
                verify=self.api_common_requests_fields.verify,
                data=self.api_common_requests_fields.data,
                body=self.api_common_requests_fields.body,
            )
            # evaluate the template
            request_template = self.template_service.get_request_template(
                template_path,
                self._convert_request_args(request_args),
            )
            # Execute login if required
            if (
                self.api_common_requests_fields.requires_login
                and request_template.requires_auth
                and not self.api_auth_data
            ):
                self.login()
            # Else if request requires auth
            elif request_template.requires_auth:
                # Verify target has auth
                if self.target.auth_data is None:
                    msg = f"Request {template_path} requires authentication to be provided with the target."
                    raise RuntimeError(msg)
                self.api_auth_data = self.target.auth_data

            # Inject auth data
            prepared_request = self._inject_auth(prepared_request)

            # Inject version
            if self.api_common_requests_fields.requires_version and request_template.requires_version:
                prepared_request = self._inject_version(prepared_request)
            # Build request from template
            prepared_request = self.template_service.build_request_from_request_template(
                request_template,
                prepared_request,
                self.target.version,
            )
            # Execute anything required for write_action
            if request_template.write_action:
                self._on_write_action(Path(template_path), request_template, prepared_request)
            # Execute requests with retries
            res = self._execute_request_with_retries(prepared_request, response_processor=response_processor)
            # Write res to cache if response is cacheable
            if self._is_response_cacheable(prepared_request, res):
                self.cache_service.set(
                    target=self.target,
                    template_path=Path(template_path),
                    response=res,
                    request_args=to_json(request_args),
                )
            return res
        # Clear request memory
        finally:
            self._current_request = None
            self._current_target = None

    # PRIVATE METHODS

    def _extract_version_from_response(self, res: Response) -> Version | None:
        """Extract version data from a "get_version" response and return it.
        Should be overriden by subclass.
        """
        raise NotImplementedError

    def _extract_auth_from_response(self, res: Response) -> None:
        """Extract auth data from a "login" response and set the attribute "api_auth_data".
        May be overriden by subclass.
        """
        raise NotImplementedError

    def _inject_auth(self, prepared_request: Request) -> Request:
        """Inject auth data into an prepared request. May be overriden by subclass."""
        return prepared_request

    def _inject_version(self, prepared_request: Request) -> Request:
        """Inject version data into an prepared request. May be overriden by subclass."""
        return prepared_request

    def _proccess_response(self, res: Response) -> Response:
        """Proccess the Response object returned by the target.</br>
        Any treatment specific to an API response can be done here.</br>
        For example you can extract from res.body only the data that matters for the request</br>
        and exclude the common fields of every request of the API.</br>
        You can also raise an error if the response status is not the one expected
        Note that only RequestError will trigger a request retry.
        May be overriden by subclass.</br>
        """
        return res

    def _before_retry(self, request: Request, response: Response) -> bool:
        """Function to execute before retrying a request due to a RequestError.</br>
        This allow the exection of cleanup operations before a retry for example.</br>
        Returns whether the request should be retried or not.</br>
        May be overriden by subclass.
        """
        return response.status_code not in self.no_retries_on_status

    def _is_response_cacheable(self, request: Request, response: Response) -> bool:
        """Return whether the response of a request should be inserted into the cache or not
        May be overriden by subclass.
        """
        return True

    def _on_write_action(self, template_path: Path, request_template: RequestTemplate, request: Request) -> None:
        """Execute any action that should be ran in case of a write_action on the device
        May be overriden by subclass.
        """
        self.cache_service.delete_cache_subtree(self.target, template_path)

    def _execute_request_with_retries(
        self,
        request: Request,
        _try: int = 0,
        _error: Exception | None = None,
        response_processor: Callable[[Self, Response], Response] | None = None,
    ) -> Response:
        """Execute a fully prepared request and extract the Response object from the response.</br>
        May be overriden by subclass.
        """
        # Register the current request
        self._current_request = request
        # If there was an error and there was to many retries raise the error
        if _error and _try > self.api_common_requests_fields.retries.max_retries:
            raise _error
        # If the request is a retry wait before executing it
        if _try > 0:
            sleep(self.api_common_requests_fields.retries.delay)
            self.api_common_requests_fields.retries.update_delay()
        try:
            res = requests_request(**request.model_dump(mode="json", exclude_none=True))  # noqa: S113 False positive
        except Exception as err:
            # retry the request
            return self._execute_request_with_retries(request, _try=_try + 1, _error=err)
        try:
            # Format
            res = self._extract_res_model_from_api_response(res, response_processor)
        except RequestError as err:
            # if the _before_retry allow the retry then retry the request
            if self._before_retry(request, err.response):
                return self._execute_request_with_retries(request, _try=_try + 1, _error=err)
            # otherwise raise
            raise
        return res

    def _extract_res_model_from_api_response(
        self,
        api_response: RequestsResponse,
        response_processor: Callable[[Self, Response], Response] | None = None,
    ) -> Response:
        """Extract a Response instance from the API response. May be overriden by subclass."""
        res = {
            "status_code": api_response.status_code,
            "headers": api_response.headers,
            "cookies": api_response.cookies,
        }
        try:
            res["body"] = api_response.json()
        except Exception:
            res["text"] = api_response.text
        # Handle request specific proccessing
        if response_processor:
            return response_processor(self, Response.model_validate(res))
        return self._proccess_response(Response.model_validate(res))

    @staticmethod
    def _convert_request_args(
        request_args: BaseModel | dict[str, Any] | list[BaseModel | dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Convert all the request args to a dict[str, Any]."""
        if not request_args:
            return {}
        # list case
        if isinstance(request_args, list):
            res = {}
            old_res_len = len(res)
            for arg in request_args:
                dumped = arg.model_dump(mode="json", by_alias=True) if isinstance(arg, BaseModel) else arg
                dumped_len = len(dumped)
                res.update(dumped)
                if len(res) < old_res_len + dumped_len:
                    # TODO replace with warning
                    raise ValueError("Somme request arguments are overlapping.")
            return res
        # non list case
        return (
            request_args.model_dump(mode="json", by_alias=True) if isinstance(request_args, BaseModel) else request_args
        )

    def flush_version_cache(self) -> None:
        """Clear the cached API version.

        After calling this method the next access to :pyattr:`version`
        will trigger a fresh request to ``_private/version``.
        """
        self._version = None
