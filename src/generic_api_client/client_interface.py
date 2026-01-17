from typing import get_type_hints
from generic_api_client.api_segments import APIAggregate
from generic_api_client.models.target import Target


class ClientInterface:
    """A base class to build your Client.
    Your subclass need to redefine the field segments with a proper custom implementation of APIAggregate
    """

    segments: APIAggregate

    def __init__(self) -> None:
        segments_class = get_type_hints(self).get("segments")
        if segments_class == APIAggregate:
            msg = (
                f"Can't create {self.__class__} because field 'segments' is not typed properly."
                "You need to properly create a custom APIAggregate class."
            )
            raise RuntimeError(msg)
        self.segments = segments_class()

    def set_target(self, target: Target) -> None:
        """Set the connector target"""
        self.segments.set_target(target)
