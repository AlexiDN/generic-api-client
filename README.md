# Generic API Client

Interact with APIs through methods and pydantic models.

## Features

- Interact with an API through Pydantic models and python methods:
    - Input and Ouptut of each endpoint can be described by a Pydantic model
    - Each endpoint can be associated to a python method
    - Allow developpers to use complex APIs with the static evaluation of the code preformed by IDEs
- Comprehensive API collections using Jinja templates
- Handle API versions via template and Pydantic Model (Comming soon)
- Cache built to handle write and read requests (Comming soon)

## Installation

```bash
pip install generic-api-client
```
## Usage

See our [wiki](https://github.com/AlexiDN/generic-api-client/wiki) if you need more details about to setup your client.

An usage example can be found [here](https://github.com/AlexiDN/openstore_nextcloud_plugin/tree/dev/src/openstore_nextcloud_plugin/api).

## License 

The project is released under the MIT License.

## Project Status

> **NOTE** <br>
> The project is currently in development phase. If you have any remark or question feel free to open an Issue