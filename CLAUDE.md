# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Tasks

- **Install dependencies** (including dev tools):
  ```bash
  poetry install --dev
  ```
- **Run linter and auto‑fix**:
  ```bash
  poetry run ruff check --fix src
  ```
- **Run formatter**:
  ```bash
  poetry run ruff format src
  ```
- **Build the package** for distribution or local use:
  ```bash
  poetry build
  ```
- **Run tests** (there are no test files in the repository yet, but when added they can be executed with):
  ```bash
  poetry run pytest
  ```
  To run a single test file or function use the standard `pytest` selectors, e.g.:
  ```bash
  poetry run pytest tests/test_example.py::test_something
  ```

## Project Structure Overview

```
src/generic_api_client/
├── api_connector_interface.py   # Base connector class
├── api_segments.py               # APISegment / APIAggregate helpers
├── client_interface.py           # Base class for API clients
├── exceptions.py                # Custom exception types
├── models/                       # Pydantic models for requests, responses, authentication, etc.
│   ├── authentication.py
│   ├── api.py
│   ├── request_template.py
│   ├── requests.py
│   ├── responses.py
│   ├── target.py
│   └── model_tree.py
├── services/
│   └── template_service.py     # Jinja2 template loader & renderer
└── utils.py                     # Small helper utilities
```

### Core Concepts

1. **APIConnectorInterface**
   * Subclass this class to implement a concrete connector for a specific API.
   * Required class attributes:
     * `api_common_requests_fields` – instance of `APICommonRequestFields` describing default request parameters.
     * `templates_dir` – `Path` pointing to the directory that holds `.json.j2` request templates.
   * Must override private methods for extraction and injection if the API requires custom behaviour:
     * `_extract_version_from_response`
     * `_extract_auth_from_response`
     * `_inject_auth`
     * `_inject_version`
2. **APISegment / APIAggregate**
   * `APISegment` decorates public methods so that any `Response` object returned is automatically converted to the type hinted by the method’s `return` annotation.
   * `APIAggregate` collects segments and automatically propagates the target and version settings to all child segments.
3. **ClientInterface**
   * A thin wrapper that expects a concrete `segments` attribute (a subclass of `APIAggregate`).
   * Provides `set_target` that forwards the target to the aggregate.
4. **TemplateService**
   * Looks for files ending with `.json.j2` in `templates_dir`.
   * Renders a Jinja2 template with the supplied arguments and returns a `RequestTemplate` instance.
   * `list_templates` can be used to introspect available request templates.
5. **Request / Response Models**
   * `Request` (in `models/requests.py`) holds all HTTP request parameters.
   * `Response` (in `models/requests.py`) represents the API response.
6. **Version‑Handling**
   * `CanonicalModel` and `VersionnedModel` provide a mechanism for supporting multiple API versions.
   * When a method declares a return type that is a subclass of `CanonicalModel`, the decorator automatically converts the raw response into the appropriate versioned model based on the API version.

## Typical Workflow for Adding a New API Endpoint

1. **Create a request template** in the appropriate sub‑directory of `templates/` (e.g. `templates/users/get.json.j2`).
   * The template should output a JSON object that matches the structure expected by `RequestTemplate`.
2. **Add a public method** to the relevant segment class (e.g. `UsersSegment`).
   * Annotate the return type with the desired model.
   * Example:
   ```python
   class UsersSegment(APISegment):
       def get_user(self, user_id: str) -> UserModel:  # type: ignore[override]
           return self.execute_request("users/get", {"user_id": user_id})
   ```
3. **Register the segment** in an `APIAggregate` subclass (e.g. `MyClientSegments`).
4. **Instantiate the client** in your application code:
   ```python
   client = MyClient()
   client.set_target(Target(url="https://api.example.com"))
   user = client.segments.users.get_user("123")
   ```
5. **Run tests** (once you add them) to validate the new endpoint.

## Things to Keep in Mind

- The `execute_request` method automatically handles login and version extraction if the `APICommonRequestFields` indicates these requirements.
- The `convert_return_value_decorator` relies on **exact type hints**. If a method returns `None` or a plain `Response`, it is returned unchanged.
- When dealing with versioned responses, ensure that you have a corresponding `CanonicalModel` subclass and at least one `VersionnedModel` subclass that matches the API’s semantic version.
- The repository uses **Poetry** for dependency management; avoid mixing `pip` and `poetry` installs in the same virtual environment.
- There is currently no CI configuration in the repository; consider adding a GitHub Actions workflow that runs the lint and test steps.

---

Feel free to consult the source files directly for additional context. Happy coding!
