# Generic API Client

Interact with APIs through methods and Pydantic models.

## Features

- Interact with an API through Pydantic models and python methods:
  - Input and output of each endpoint can be described by a Pydantic model
  - Each endpoint can be associated to a python method
  - Allow developers to use complex APIs with the static evaluation of the code performed by IDEs
- Comprehensive API collections using Jinja templates
- Handle API versions via template and Pydantic Model
- Cache built to handle write and read requests

## Installation

```bash
pip install generic-api-client
```

## Usage

See our [wiki](https://github.com/AlexiDN/generic-api-client/wiki) or the new **docs** directory for detailed guidance on creating an `APIClient`, defining `Segments`, and building custom `APIConnectors`.

## Examples

The repository includes an `examples/` directory with working examples, such as the `nextcloud_api` demo. These examples demonstrate how to use the library to interact with the Nextcloud API.

## Documentation

A dedicated `docs/` directory contains markdown files that serve as a lightweight wiki, covering:

- Overview of the library
- How to instantiate an `APIClient`
- Defining custom `Segments`
- Creating `APIConnectors`
- Using the Nextcloud example

## License

The project is released under the MIT License.

## Acknowledgements

This project was built with the help of Claude Code and local Ollama AI assistants. They were used mainly for documentation so keep in mind that even if it has been reviewed it may contains errors.


## Project Status

> **NOTE**
> The project is currently in development phase. If you have any remark or question feel free to open an Issue
