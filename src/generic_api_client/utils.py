import operator
import time
from semver import Version


OPS = {
    ">=": operator.ge,
    "<=": operator.le,
    "<": operator.lt,
    ">": operator.gt,
    "==": operator.eq,
}


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
