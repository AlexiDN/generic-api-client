from typing import Optional
from pydantic import BaseModel
from treelib import Tree


class ModelTree(Tree):
    """A Tree used to store Pydantic model as data"""

    def to_json(self) -> dict:
        """Export the tree a JSON dict."""
        # dump tree with python objects
        data = self.to_dict(with_data=True)
        # dump pydantic models
        return self._dump_pydantic_model(data)

    @staticmethod
    def _dump_pydantic_model(data: dict | BaseModel) -> dict:
        if isinstance(data, BaseModel):
            return data.model_dump(mode="json", exclude_none=True)
        if isinstance(data, list):
            return [ModelTree._dump_pydantic_model(item) for item in data]
        if isinstance(data, dict):
            return {key: ModelTree._dump_pydantic_model(value) for key, value in data.items()}
        return data

    @classmethod
    def from_json(
        cls,
        json: dict,
        base_tree: Optional["ModelTree"] = None,
        parent: list | None = None,
        node_data_model: BaseModel | None = None,
    ) -> "ModelTree":
        """Build a ModelTree from json data.
        A base tree and a parent can be specified
        as well as the Pydantic data_model to build python objects as node data
        """
        # Verify only one root
        if len(json.keys()) != 1:
            msg = f"Tree have one and only one root. {len(json.keys())} were provided."
            raise ValueError(msg)
        # Create empty tree if needed
        tree = base_tree or ModelTree()
        # Create node
        node_id = next(iter(json.keys()))
        node_children, node_data = json.get(node_id).get("children", []), json.get(node_id).get("data")
        # build object from data if model is provided
        if node_data and node_data_model:
            node_data = node_data_model.model_validate(node_data, by_alias=True)
        node = tree.create_node(tag=node_id, identifier=node_id, parent=parent, data=node_data)
        # Recursively create children nodes
        for child_data in node_children:
            cls.from_json(json=child_data, base_tree=tree, parent=node.identifier, node_data_model=node_data_model)
        return tree
