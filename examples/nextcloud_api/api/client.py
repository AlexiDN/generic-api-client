from generic_api_client import ClientInterface

from .segments.all import NextCloudAPISegments


class NextCloudClient(ClientInterface):
    segments: NextCloudAPISegments
