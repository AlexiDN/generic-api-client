# Nextcloud Example

To see the full result go [here](https://github.com/AlexiDN/openstore_nextcloud_plugin/tree/main/src/openstore_nextcloud_plugin/api)

## I - How to structure your code

Bellow is an example on how to structure your client component.

```
├── api_connector.py
├── client.py
├── templates (All the jinja templates to describe the API requests)
│   ├── ocs
│   │   └── groups/../ (I prefer to follow the API structure to order the template)
│   │   │   └── list.json.j2 (the templates must have the .json.j2 extension)
│   ├── _private ( folder for login and get_version tasks)
│   │   └── login.json.j2
│   └── other templates...
├── models (All the input and output Pydantic models)
│   ├── ocs
│   │   └── groups/../
│   │   │   └── list.py
│   └── other input/output models...
├── segments (All the APISegments and APIAggregates)
│   ├── interfaces.py (Usually where you store your base APIAggregate class that define the APIConector for your API)
│   ├── all.py (The main APIAggregate that rule them all)
│   ├── ocs 
│   │   └── groups/../(Here you should follow the same structure as the models )
│   │   │   └── groups.py 
│   └── other APISegments and APIAggregate ...
```
## II - Create your request templates library

Create json jinja templates for all the endpoints you want.

Any request template follow this structure:

```py
class RequestOptions(BaseModel):
    endpoint: str = Field("", description="The endpoint path")
    method: HTTPMethod | None = None
    headers: dict[str, Any] | None = None
    params: list[list[str, Any]] | None = None
    cookies: dict[str, Any] | None = None
    body: dict | str | None = None

class RequestTemplate(BaseModel):
    requires_auth: bool = Field(True, description="Either the request requires authentication or not.")
    requires_version: bool = Field(False, description="Either the request requires API version or not.")
    general_options: RequestOptions | None = Field(description="Options which are common to all versions of the API.")
    version_options: dict[str, RequestOptions] = Field(
        description="Options that depends on some API versions.", default_factory=dict
    )
```
Example:
```json
{
    "general_options":{
        "endpoint": "/ocs/v2.php/cloud/groups",
        "method": "GET",
        "params": [["search", "{{ SEARCH }}"],["limit", "{{ LIMIT }}"],["offset", "{{ OFFSET }}"]]
    }
}
```
## III - Build your APIConector

To build a concrete connector you subclass :class:`generic_api_client.api_connector_interface.APIConectorInterface` and define the required class attributes:

* ``api_common_requests_fields`` – an instance of :class:`generic_api_client.models.api.APICommonRequestFields` that contains the default URL root, default headers, timeout, etc.
* ``templates_dir`` – :class:`pathlib.Path` pointing to the folder that holds the Jinja2 request templates.

During construction the base class initialises a :class:`generic_api_client.services.template_service.TemplateService` pointing at that directory. You also have to override the private methods that depend on the particular API (extracting auth, injecting auth, extracting version, etc.).

Example implementation for a Nextcloud connector:

```python
from pathlib import Path
from generic_api_client.api_connector_interface import APIConectorInterface
from generic_api_client.services.template_service import TemplateService
from generic_api_client.models.api import APICommonRequestFields

class NextcloudConnector(APIConectorInterface):
    api_common_requests_fields = APICommonRequestFields(
        root_url="/ocs/v2.php",
        method="GET",
        requires_login=True,
        requires_version=True,
        # …other default options…
    )
    templates_dir = Path(__file__).parent / "templates"

    def _extract_auth_from_response(self, res):
        # parse login response and store credentials
        self.api_auth_data = res.body["token"]

    def _extract_version_from_response(self, res):
        return res.body["version"]
```
The connector is now ready to be used by a :class:`generic_api_client.api_segments.APIAggregate`.
## IV - Create the Client

### Define your segments
Create a subclass of :class:`generic_api_client.api_segments.APIAggregate` that contains the segments you want to expose. Each segment is itself a subclass of :class:`generic_api_client.api_segments.APISegment`. The aggregate must specify a ``connector`` type hint so that the base class can instantiate it.

```python
from generic_api_client.api_segments import APIAggregate, APISegment
from .api_connector import NextcloudConnector

class GroupsSegment(APISegment):
    # you can add custom methods here
    pass

class NextcloudAPI(APIAggregate):
    connector: NextcloudConnector
    groups: GroupsSegment
```

### Create the methods
In a segment class you add public methods that wrap :meth:`_execute_request`. The method signature should include the parameters required by the Jinja template and the return type hint of the expected Pydantic model.

```python
class GroupsSegment(APISegment):
    def list(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> GroupsListResponse:
        args = {
            "SEARCH": search,
            "LIMIT": limit,
            "OFFSET": offset,
        }
        return self._execute_request("ocs/groups/list", args)
```

The decorator added by :class:`APISegment` will automatically convert the raw ``Response`` into the ``GroupsListResponse`` Pydantic model.

### Create the input and output Pydantic Models

Define the request and response models in ``src/generic_api_client/models/``.

For responses that vary between API versions the library uses a *canonical* model and a set of *version‑specific* models:

* **CanonicalModel** – represents the public API surface. It can expose fields that exist only on some versions. These fields are defined directly on the canonical model.
* **Version‑specific models** – one class per supported API version. They inherit directly from `VersionnedModel` and contain only the fields that are present in that version. The canonical model holds a list of these subclasses in ``_versionned_models``. At runtime the library picks the appropriate subclass, validates the raw response, and then converts the result into the canonical model before returning it to the caller.

Example – the Nextcloud *apps* endpoint:

```python
# src/generic_api_client/models/apps/list.py
from pydantic import BaseModel
from generic_api_client.models.responses import CanonicalModel, VersionnedModel

# Canonical model – what the public API exposes
class NextCloudAppsList(CanonicalModel):
    apps: list[str]

# Version‑specific models – one per supported API version
class NextCloudAppsList_1(VersionnedModel):
    __version__ = Version.parse("32")
    apps: list[str]

class NextCloudAppsList_2(VersionnedModel):
    __version__ = Version.parse("10")
    apps: list[str]

# Register the version‑specific models
NextCloudAppsList._versionned_models = [NextCloudAppsList_1, NextCloudAppsList_2]
```

The segment method simply declares the canonical return type:

```python
class NextCloudApps(NextCloudAPIBaseAggregate):
    def list_installed_apps(self) -> NextCloudAppsList:
        return self._execute_request("ocs/v2_php/cloud/apps/list")
```

When the request is executed, the library will pick the correct `NextCloudAppsList_X` class based on the API version, validate the JSON, then convert it into a `NextCloudAppsList` instance that is returned to the caller.

### Define the client class

Finally create a concrete client that subclasses :class:`generic_api_client.client_interface.ClientInterface` and provides the ``segments`` attribute pointing to your aggregate.

```python
from generic_api_client.client_interface import ClientInterface
from .segments import NextcloudAPI

```

Now you can use the client like:

```python
client = NextcloudClient(cache_ttl_seconds=60)
client.set_target(Target(url="https://nextcloud.example.com", auth_data=Token("...")), extract_version=True)
result = client.segments.groups.list(search="dev")
print(result)
```
## V - Cache Backend

The `ClientInterface` constructor accepts `cache_ttl_seconds` and an optional `redis_client`.  
* When you **only** provide a TTL, the client automatically creates an **in‑memory** `ExpiringDictCacheRepository` via `CacheService`.  
* If you also pass a `redis.Redis` (or compatible) instance, the client uses a **RedisCacheRepository** so all cache operations are forwarded to Redis, giving you a shared, persistent cache across processes.

```python
# ClientInterface constructor
client = ClientInterface(cache_ttl_seconds=60)  # in‑memory cache
client = ClientInterface(cache_ttl_seconds=60,
                         redis_client=redis.Redis(host="localhost", port=6379))  # Redis cache
```

### How to enable Redis in the example
```python
import redis
from generic_api_client.services.cache_service import CacheService

redis_client = redis.Redis(host="localhost", port=6379)
# The example client automatically passes this to the constructor
client = NextcloudClient(cache_ttl_seconds=60, redis_client=redis_client)
```

## VI - Example: Listing Apps

The Nextcloud example demonstrates the full flow.  The `NextCloudApps` segment exposes a `list_installed_apps` method that returns a **canonical** model `NextCloudAppsList`.  Internally the library fetches the raw response, detects the API version, builds the version‑specific model (`NextCloudAppsList_1` or `NextCloudAppsList_2`), and the `APISegment` decorator converts it to the canonical form before returning it.

```python
from examples.nextcloud_api.api.client import NextCloudClient
from examples.nextcloud_api.api.segments.apps.apps import NextCloudApps

# Instantiate the client and set target
client = NextCloudClient(cache_ttl_seconds=60)
client.set_target(Target(url="https://nextcloud.example.com",
                        auth_data=Token("user", "pass")),
                extract_version=True)

# Call the method
installed = client.segments.apps.list_installed_apps()
print(installed.apps)  # list of installed app IDs
```

The `installed` object is a `NextCloudAppsList` instance, which inherits from `CanonicalModel`.  You can safely use it across different API versions, and the library guarantees that the underlying JSON structure is normalised.
