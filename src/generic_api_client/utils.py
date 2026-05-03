from enum import Enum
import operator
import time
from pydantic import BaseModel, TypeAdapter
from semver import Version
import sys
import types
import typing
from collections.abc import Container, Iterable, Mapping

OPS = {
    ">=": operator.ge,
    "<=": operator.le,
    "<": operator.lt,
    ">": operator.gt,
    "==": operator.eq,
}


class ResponseSource(str, Enum):
    CACHE = "CACHE"
    API = "API"


JSONPrimitive: typing.TypeAlias = str | int | float | bool
JSONType: typing.TypeAlias = JSONPrimitive | list["JSONType"] | dict[str, "JSONType"]


def to_json(
    obj: BaseModel | dict[str, typing.Any] | list[BaseModel | dict[str, typing.Any]] | None,
) -> JSONType | None:
    """Serialize an object to a JSONType"""
    if obj is None:
        return obj
    if isinstance(obj, BaseModel):
        obj = obj.model_dump(mode="python")

    return TypeAdapter(JSONType).dump_python(
        obj,
        mode="json",
    )


def check_constraint(version: Version, constraint: str) -> bool:
    """Return either the version satisfies the constraint.
    Note that it only supports 'and' between arithmetic operators.
    """
    parts = [p.strip() for p in constraint.split("and")]

    for part in parts:
        for op_str, op_func in OPS.items():
            if part.startswith(op_str):
                target = Version.parse(part[len(op_str) :].strip())
                if not op_func(version, target):
                    return False
                break
        else:
            msg = f"Unknown constraint: {part}"
            raise ValueError(msg)
    return True


def get_current_time() -> int:
    """Return the current time in seconds since the Epoch."""
    return int(time.time())


# Code from https://github.com/notarealdeveloper/is-instance/blob/master/src/is_instance/main.py
def is_instance(obj: typing.Any, cls: type) -> bool:  # noqa: C901, PLR0911
    """Return whether the object is an instance of the class. It handles nested types."""
    if isinstance(cls, tuple):
        return any(is_instance(obj, sub) for sub in cls)

    if sys.version_info >= (3, 10) and isinstance(cls, types.UnionType):
        return any(is_instance(obj, sub) for sub in cls.__args__)

    if cls is None:
        cls = types.NoneType

    if not isinstance(cls, (types.GenericAlias, types.GenericAlias)):
        return isinstance(obj, cls)

    cls_origin = typing.get_origin(cls)
    cls_args = typing.get_args(cls)

    if isinstance(cls, typing._LiteralGenericAlias):  # noqa: SLF001
        return obj in cls_args

    if not is_instance(obj, cls_origin):
        return False

    if issubclass(cls_origin, tuple):
        if len(cls_args) != len(obj):
            return False
        return all(map(is_instance, obj, cls_args))

    if issubclass(cls_origin, Mapping) and len(cls_args) == 2:  # noqa: PLR2004
        key_type, val_type = cls_args
        return all(is_instance(key, key_type) and is_instance(val, val_type) for key, val in obj.items())

    if issubclass(cls_origin, (Container, Iterable)) and len(cls_args) == 1:
        [inner_type] = cls_args
        if len(obj):
            return all(is_instance(item, inner_type) for item in obj)
        return is_instance(obj, inner_type) or hasattr(obj, "__class_getitem__")

    raise TypeError(obj, cls)
