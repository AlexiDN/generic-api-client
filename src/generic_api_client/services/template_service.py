from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template
from semver import Version
from generic_api_client.models.request_template import RequestTemplate
from generic_api_client.models.requests import Request

# Templates file extensions
FILE_EXTENSION = ".json.j2"


class TemplateService:
    # The root directory of the templates
    templates_root_dir: Path
    # The storage used for the raw template before if is rendered
    raw_template: Template

    def __init__(self, templates_root_dir: Path) -> None:
        self.templates_root_dir = templates_root_dir

    def _read_template(self, template_path: str) -> None:
        """Read a template an store it as raw Template object"""
        if not self.templates_root_dir.joinpath(template_path + FILE_EXTENSION).exists():
            raise FileNotFoundError("Request template %s does not exist", template_path)
        env = Environment(loader=FileSystemLoader(self.templates_root_dir), autoescape=True)
        self.raw_template = env.get_template(template_path + FILE_EXTENSION)

    def get_request_template(self, template_path: str, template_args: dict[str, Any]) -> RequestTemplate:
        """Return the request template evaluated with the template_args given."""
        self._read_template(template_path)
        rendered_data = self.raw_template.render(**template_args)
        request_template = json.loads(rendered_data)
        return RequestTemplate.model_validate(request_template)

    def list_templates(self, sub_dir: str = "") -> list[Path]:
        """List all the templates available for a subdir of the template_root_dir."""
        search_dir = self.templates_root_dir.joinpath(sub_dir)
        return list(search_dir.glob("**.json.j2"))

    @staticmethod
    def build_request_from_request_template(
        request_template: RequestTemplate, base_request: Request, version: Version | None = None
    ) -> Request:
        """Build the request from the request template and the base_request"""
        request_options = request_template.get_final_request_options(version)
        request = deepcopy(base_request)
        request.update_url_with_uri(request_options.endpoint)
        request.update_method(request_options.method or request.method)
        request.update_headers(request_options.headers or {})
        request.update_params(request_options.params)
        if request_options.body is not None:
            if isinstance(request_options.body, str):
                request.update_data(request_options.body)
            else:
                request.update_json(request_options.body)
        request.update_cookies(request_options.cookies or {})
        return request
