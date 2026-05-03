import base64
from http import HTTPStatus
from pathlib import Path

from semver import Version
from generic_api_client import APIConectorInterface, APICommonRequestFields, Request, Response, RequestError


class NextCloudAPIConnector(APIConectorInterface):
    api_common_requests_fields = APICommonRequestFields(
        headers={
            "OCS-APIRequest": "true",
            "Accept": "application/json",
        },
        retries={"delay": 0, "max_retries": 1},
    )

    templates_dir = Path(__file__).parent.joinpath("templates")

    def execute_request(
        self, template_path, request_args=None, target_override=None, response_processor=None, use_cache=True
    ):
        res = super().execute_request(template_path, request_args, target_override, response_processor, use_cache)
        print(f"Result Source: {res.source}")
        return res

    def extract_version(self) -> Version:
        """Retrieve of the API version"""

        def version_proccessor(connector: APIConectorInterface, res: Response) -> Response:
            """Proccess the response for the version request"""
            # verify that the request succeed
            if res.status_code != HTTPStatus.OK:
                raise RequestError("Request failed.", res, connector._current_request)  # noqa: SLF001
            return res

        try:
            # execute get_version
            res = self.execute_request("_private/version", response_processor=version_proccessor)
            # set version from response
            version = self._extract_version_from_response(res)
        except FileNotFoundError as err:
            msg = f"Can't execute required 'load_version' because the task where not found. Exc:{err}"
            raise RuntimeError(msg) from err
        else:
            self._version = version
            return version

    def _inject_auth(self, prepared_request: Request) -> Request:
        """Inject basic auth into the prepared_request"""
        # extract credentials from api_auth_data
        credentials = f"{self.api_auth_data.username}:{self.api_auth_data.password}"
        # Encode in base64
        encoded = base64.b64encode(credentials.encode()).decode()
        # Add Authorization header
        prepared_request.update_headers({"Authorization": f"Basic {encoded}"})
        return prepared_request

    def _extract_version_from_response(self, res: Response) -> Version | None:
        """Extract version data from a "get_version" response and return it.
        Shoul be overriden by subclass.
        """
        return Version.parse(res.body.get("versionstring", "Unknown"))

    def _before_retry(self, request: Request, response: Response) -> bool:  # noqa: ARG002
        # execute password confirmation if it is required
        if (
            response.status_code == HTTPStatus.FORBIDDEN
            and response.body.get("ocs", {}).get("meta", {}).get("message") == "Password confirmation is required"
        ):
            self.execute_request("_private/confirm_password", {"PASSWORD": self.api_auth_data.password})
            return True
        # if the the error does not come from passsword required then do not retry
        return False

    def _proccess_response(self, res: Response) -> Response:
        # verify that the request succeed
        if (
            res.status_code != HTTPStatus.OK
            or res.body.get("ocs", {}).get("meta", {}).get("status", "").lower() != "ok"
        ):
            raise RequestError("Request failed.", res, self._current_request)
        # extract data from the res.body
        res.body = res.body.get("ocs", {}).get("data", {})
        return super()._proccess_response(res)
