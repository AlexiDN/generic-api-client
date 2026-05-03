from .apps.apps import NextCloudApps
from .groups.groups import NextCloudGroups
from .interfaces import NextCloudAPIBaseAggregate


class NextCloudAPISegments(NextCloudAPIBaseAggregate):
    apps: NextCloudApps
    groups: NextCloudGroups
