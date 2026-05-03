from examples.nextcloud_api.api.models.apps.list_result import NextCloudAppsList
from examples.nextcloud_api.api.segments.apps.group_folders import NextCloudAppGroupFolders
from examples.nextcloud_api.api.segments.apps.user_ldap import NextCloudAppUserLdap
from examples.nextcloud_api.api.segments.interfaces import NextCloudAPIBaseAggregate


class NextCloudApps(NextCloudAPIBaseAggregate):
    user_ldap: NextCloudAppUserLdap
    group_folders: NextCloudAppGroupFolders

    def list_installed_apps(self) -> NextCloudAppsList:
        """List all the apps installed"""
        return self._execute_request("ocs/v2_php/cloud/apps/list")

    def enable_app(self, app_name: str) -> None:
        """Enable an app"""
        return self._execute_request("ocs/v2_php/cloud/apps/enable", {"APP_NAME": app_name})

    def disable_app(self, app_name: str) -> None:
        """Disable an app"""
        return self._execute_request("ocs/v2_php/cloud/apps/disable", {"APP_NAME": app_name})
