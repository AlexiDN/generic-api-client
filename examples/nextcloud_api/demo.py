from time import sleep

from semver import Version

from generic_api_client.models.target import Target
from examples.nextcloud_api.api.client import NextCloudClient
from examples.nextcloud_api.api.models.apps.list_result import NextCloudAppsList


client = NextCloudClient(cache_ttl_seconds=10)


client.set_target(
    Target(
        url="nextcloud_server_url",
        auth_data={"username": "nextcloud_username", "password": "nextcloud_password"},
    ),
    extract_version=False,  # Do not need to extract version
)


# CACHE TESTS
print("\n\nCACHE TESTS\n\n")
print("First request")  # ->Source should be API
apps = client.segments.apps.list_installed_apps()
assert isinstance(apps, NextCloudAppsList)
print("\nSecond request")  # ->Source should be CACHE
apps = client.segments.apps.list_installed_apps()
assert isinstance(apps, NextCloudAppsList)
print("\nSleep")
sleep(10)
print("\nThird request")  # ->Source should be API
apps = client.segments.apps.list_installed_apps()
assert isinstance(apps, NextCloudAppsList)


client.set_target(
    Target(
        url="nextcloud_server_url",
        auth_data={"username": "nextcloud_username", "password": "nextcloud_password"},
    ),
    extract_version=True,  # Need to extract version here
)

# VERSIONS TESTS
print("\n\nVERSIONS TESTS\n\n")


print(f"CANONICAL VERSION->{apps.__class__.__name__}")  # Cfass should be the canonical one
print(
    f"TO Version 10->{apps.to_version(Version(10)).__class__.__name__}"
)  # Class should be the one associated to semver 10.0.0

print("####TARGET")
print(client.segments.connector.target.version)  # See that version is stored in target

print("####ROOT")
print(client.segments.version)  # See that the segment can display a version
print(client.segments._segment_version)  # See that root segment hold the version it displays

print("####APPS")
print(client.segments.apps.version)  # See that the segment can display a version
print(
    client.segments.apps._segment_version
)  # See that this segment doesn't hold the version it displays since there is no override
