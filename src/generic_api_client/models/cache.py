import hashlib
import json
from pathlib import Path
from pydantic import BaseModel, SerializationInfo, field_serializer, model_validator, Field

from generic_api_client.models.authentication import Credentials, Token
from generic_api_client.models.model_tree import ModelTree
from generic_api_client.models.requests import Response
from treelib import Node
from generic_api_client.utils import get_current_time


class CacheResponse(BaseModel):
    res: Response = Field(description="API response")
    expiration_time: int = Field(get_current_time(), description="Expiration time of the entry")


class CacheTree(ModelTree):
    """A ModelTree used as cache to store API responses"""

    def clear(self) -> None:
        """Clear the cache tree"""
        self.remove_node("root")

    def set_response(self, path: Path, res: CacheResponse) -> None:
        """Add a Cache response to the tree using its path."""
        key = self._key_from_path(path)
        # set response if node already exist
        node = self.get_node(key)
        if node:
            node.data = res
        # Create the parent branch if node does not exist
        parent = self._create_parent_branch_from_path(path)
        # create the node
        self.create_node(key, key, parent=parent, data=res)

    def get_response(self, path: Path) -> CacheResponse | None:
        """Get a CacheResponse from a path.
        Returns None if the path does not exist or does not contains data.
        """
        node: Node = self.get_node(self._key_from_path(path))
        if node and node.data:
            data: CacheResponse = node.data
            if get_current_time() < data.expiration_time:
                return data
            # delete cached response if it expired
            self.delete_response(path)
        return None

    def delete_response(self, path: Path) -> None:
        """Delete a response from a Path"""
        self.remove_node(self._key_from_path(path))

    def _create_parent_branch_from_path(self, path: Path) -> Node:
        """Create the nodes required for the path asked as input.
        Return the last node of the path
        """
        str_path = str(path.with_suffix("")).removeprefix("root")
        parts = str_path.split("/")
        current_path = "root"
        parent = None
        search = True
        for part in parts:
            # Search if a node exist with this path
            if search and self.contains(current_path):
                parent = self[current_path]
            # Create the node and set it as new parent
            else:
                search = False  # Disable search of existence since it will be false
                parent = self.create_node(current_path, current_path, parent=parent)
            current_path += f"/{part}"
        # Return last created node
        return parent

    @staticmethod
    def _key_from_path(path: Path) -> str:
        """Generate a key from a path"""
        return "root/" + str(path)


class TargetCache(BaseModel, arbitrary_types_allowed=True):
    auth_data: Credentials | Token | None = None
    responses_tree: CacheTree

    def clear(self, clear_auth_data: bool = False) -> None:
        """Clear the responses tree cache and optionaly the authentication data."""
        if clear_auth_data:
            self.auth_data = None
        self.responses_tree.clear()

    def get_response(self, template_path: Path, request_args: dict) -> CacheResponse:
        """Retrieve a cached response from the response tree"""
        self.responses_tree.get_response(self._path_from_request_infos(template_path, request_args))

    def delete_response(self, template_path: Path, request_args: dict) -> None:
        """Delete a cached response from the response tree"""
        self.responses_tree.delete_response(self._path_from_request_infos(template_path, request_args))

    def set_response(self, template_path: Path, request_args: dict, response: CacheResponse) -> None:
        """Add a response into the response tree"""
        self.responses_tree.set_response(self._path_from_request_infos(template_path, request_args), response)

    @staticmethod
    def _path_from_request_infos(template_path: Path, request_args: dict) -> Path:
        """Create a unique cache path from request path and args"""
        return template_path.with_suffix("").joinpath(hashlib.sha256(json.dumps(request_args).encode()).hexdigest())

    # Pydantic serializers and validators

    @field_serializer("responses_tree", when_used="json")
    @staticmethod
    def serialize_responses_tree(responses_tree: ModelTree, _info: SerializationInfo) -> dict:
        """Serialize 'responses_tree' to dict"""
        return responses_tree.to_json(with_data=True)

    @model_validator(mode="before")
    @classmethod
    def create_responses_tree(cls, data: dict) -> dict:
        """Create the responses_tree from a dict"""
        if not data.get("responses_tree"):
            raise ValueError("Missing field 'responses_tree'.")
        # Create Tree instance from data.responses_tree
        try:
            data["responses_tree"] = ModelTree.from_json(data.get("responses_tree"), node_data_model=CacheResponse)
        except Exception as err:
            msg = f"Failed to create 'responses_tree'. Caused by: {err}"
            raise ValueError(msg) from err
        return data
