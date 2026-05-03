from generic_api_client import APIAggregate

from examples.nextcloud_api.api.api_connector import NextCloudAPIConnector


class NextCloudAPIBaseAggregate(APIAggregate):
    connector: NextCloudAPIConnector
