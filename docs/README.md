# Library Documentation

This directory contains a lightweight wiki that explains how to use **generic-api-client** in depth. Each section focuses on a core concept and provides example snippets.

## Table of Contents

- [Overview](#overview)
- [Creating an APIClient](#creating-an-apiclient)
- [Defining Segments](#defining-segments)
- [Building APIConnectors](#building-apiconnectors)
- [Nextcloud API Example](#nextcloud-api-example)
- [Contributing](#contributing)

---

## Overview

`generic-api-client` is a framework that lets you wrap any RESTful API in a strongly‑typed Python client.  It relies on

- **Pydantic models** for request/response validation
- **Jinja2 templates** for request bodies and URLs
- **Segmentation** to organize endpoints into logical groups
- Optional **caching** and **version handling** hooks

The library ships with an example implementation for the Nextcloud API in the `examples/nextcloud_api` directory.  That example shows all of the building blocks in action.

## Creating an APIClient

```python
from pathlib import Path
from generic_api_client.client_interface import ClientInterface
from generic_api_client.services.template_service import TemplateService
from generic_api_client.models.target import Target

# Create a concrete client by inheriting ClientInterface
class MyClient(ClientInterface):
    segments: MySegments  # type: ignore

# Instantiate the client
client = MyClient()
client.set_target(Target(url="https://api.example.com"))
```

The `ClientInterface` only requires a `segments` attribute that is an `APIAggregate`.  The aggregate holds the segment objects.

## Defining Segments

Segments are subclasses of `APISegment` that expose typed methods.  Each method typically calls `execute_request` and returns a Pydantic model.

```python
from generic_api_client.api_segments import APISegment

class UsersSegment(APISegment):
    def get_user(self, user_id: str) -> UserModel:  # type: ignore[override]
        return self.execute_request("users/get", {"user_id": user_id})
```

The string argument to `execute_request` refers to a template name under the connector’s `templates_dir`.

## Building APIConnectors

An `APIConnectorInterface` implements the low‑level HTTP plumbing and any custom request/response logic.

```python
from generic_api_client.api_connector_interface import APIConnectorInterface
from generic_api_client.services.template_service import TemplateService
from pathlib import Path

class MyConnector(APIConnectorInterface):
    api_common_requests_fields = ...  # fill in defaults
    templates_dir = Path(__file__).parent / "templates"
    template_service = TemplateService(templates_dir)

    # override extraction/injection hooks if needed
```

Once you have a connector, you can plug it into the client and use the segments.

## Nextcloud API Example

The `examples/nextcloud_api` folder contains a fully‑worked client that uses the library to call Nextcloud endpoints.  Key files:

- `api_connector.py` – concrete connector with Nextcloud‑specific headers and auth.
- `client.py` – client that aggregates the Nextcloud segments.
- `segments/` – segment modules such as `apps.py` and `groups.py`.
- `templates/` – Jinja2 JSON templates for each endpoint.

Run the example:

```bash
poetry install
python examples/nextcloud_api/client.py
```

This will instantiate the client, set a target URL, and demonstrate a few API calls.

## Contributing

Feel free to open issues or PRs.  The library is still in development, so documentation and examples are welcome.
