from contextvars import Token
from http import HTTPMethod
from pathlib import Path
from typing import ClassVar
from pydantic import BaseModel
from requests import Response as RequestsResponse, request
from .models.authentication import Credentials
from .models.requests import Request, Response
from .models.api import APICommonRequestFields
from semver import Version

from .models.target import Target
from .services.template_service import TemplateService


class APIConectorInterface:
    # Class fields
    api_common_requests_fields: ClassVar[APICommonRequestFields] = None
    templates_dir: Path = None
    template_service: TemplateService
    # Instance fields
    # Field initialized by login method
    api_auth_data: Credentials | Token | None = None
    # Field initialized by get_version method
    version: Version | None = None
    # Field definining on which target to execute the api
    target: Target | None = None

    # CONSTRUCTOR
    def __new__(cls) -> "APIConectorInterface":
        """Verify that the class implementation is correct before building an instance."""
        if not hasattr(cls, "api_common_requests_fields"):
            msg = f"Can't instantiate {cls} because api_common_requests_fields field needs to be defined."
            raise RuntimeError(msg)
        if not hasattr(cls, "templates_dir"):
            msg = f"Can't instantiate {cls} because templates_dir field needs to be defined."
            raise RuntimeError(msg)
        cls.template_service = TemplateService(Path(cls.templates_dir))
        return super().__new__(cls)

    # PUBLIC METHODS
    def set_target(self, target: Target) -> None:
        """Set self.target"""
        self.target = target

    def get_target(self) -> Target:
        """Return self.target"""
        return self.target

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

    def extract_version(self) -> None:
        """Retrieve of the API version"""
        try:
            # execute get_version
            res = self.execute_request("_private/version")
            # set version from response
            self._extract_version_from_response(res)
        except FileNotFoundError as err:
            msg = f"Can't execute required 'load_version' because the task where not found. Exc:{err}"
            raise RuntimeError(msg) from err

    def execute_request(self, template_path: str, task_args: BaseModel | None = None) -> Response:
        """Execute a request base on a template name"""
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
            json=self.api_common_requests_fields.json,
        )
        request_template = self.template_service.get_request_template(
            template_path,
            task_args.model_dump(mode="json", by_alias=True, exclude_unset=True) if task_args else {},
        )
        # Execute login if required
        if self.api_common_requests_fields.requires_login and request_template.requires_auth and not self.api_auth_data:
            self.login()
        # Else if request requires auth
        elif request_template.requires_auth:
            # Verify target has auth
            if self.target.auth_data is None:
                msg = f"Request {template_path} requires authentication to be provided with the target."
                raise RuntimeError(msg)
            self.api_auth_data = self.target.auth_data
        # Execute get_version if required
        if self.api_common_requests_fields.requires_version and request_template.requires_version and not self.version:
            self.extract_version()
        # Inject version and auth data
        prepared_request = self._inject_auth(prepared_request)
        prepared_request = self._inject_version(prepared_request)
        # Build request from template
        prepared_request = self.template_service.build_request_from_request_template(
            request_template, prepared_request, self.version
        )
        # Send request
        res = request(**prepared_request.model_dump(mode="json", exclude_none=True))  # noqa: S113 (False positive)
        # Convert to Response Model
        return self._extract_res_model_from_api_response(res)

    # PRIVATE METHODS

    def _extract_version_from_response(self, res: Response) -> None:
        """Extract version data from a "get_version" response and set the attribute "version".
        May be overriden by subclass.
        """

    def _extract_auth_from_response(self, res: Response) -> None:
        """Extract auth data from a "login" response and set the attribute "api_auth_data".
        May be overriden by subclass.
        """

    def _inject_auth(self, prepared_request: Request) -> Request:
        """Inject auth data into an prepared request. May be overriden by subclass."""
        return prepared_request

    def _inject_version(self, prepared_request: Request) -> Request:
        """Inject version data into an prepared request. May be overriden by subclass."""
        return prepared_request

    def _format_response(self, res: Response) -> Response:
        """Format the Response object returned by the target. May be overriden by subclass.</br>
        Any treatment specific to an API response can be done here.</br>
        For example you can extract from res.json only the data that matters for the request
        and exclude the fields in common for every request of the API.
        """
        return res

    def _extract_res_model_from_api_response(self, api_response: RequestsResponse) -> Response:
        """Extract a Response instance from the API response. May be overriden by subclass."""
        res = {
            "status_code": api_response.status_code,
            "headers": api_response.headers,
            "cookies": api_response.cookies,
        }
        try:
            res["json"] = api_response.json()
        except Exception:
            res["text"] = api_response.text
        return self._format_response(Response.model_validate(res))
