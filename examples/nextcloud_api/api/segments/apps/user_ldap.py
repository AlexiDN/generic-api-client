from generic_api_client import APISegment

from examples.nextcloud_api.api.models.apps.user_ldap.ldap_config import LDAPConfigModel


class NextCloudAppUserLdap(APISegment):
    def _create_empty_config(self) -> str:
        """Create an empty config and return the config id."""
        res = self._execute_request("ocs/v2_php/apps/user_ldap/create_empty_config")
        return res.body.get("configID")

    def create_ldap_config(self, ldap_config: LDAPConfigModel) -> str:
        """Create an ldap config then return the id"""
        config_id = self._create_empty_config()
        self.update_ldap_config(config_id, ldap_config)
        return config_id

    def update_ldap_config(self, config_id: str, ldap_config: LDAPConfigModel) -> None:
        """Modify an existing ldap config."""
        return self._execute_request(
            "ocs/v2_php/apps/user_ldap/modify_config",
            {"CONFIG_ID": config_id, "CONFIG_DATA": ldap_config.model_dump(mode="json", exclude_none=True)},
        )

    def get_ldap_config(self, config_id: str, show_password: bool = False) -> LDAPConfigModel:
        """Return the ldap config associated to a config_id"""
        return self._execute_request(
            "ocs/v2_php/apps/user_ldap/get_config",
            {"CONFIG_ID": config_id, "SHOW_PASSWORD": show_password},
        )
