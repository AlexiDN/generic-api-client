from __future__ import annotations
from pydantic import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openstoreplugin import LdapConfig


class LDAPConfigModel(BaseModel):
    ldapHost: str
    ldapPort: str
    ldapBackupHost: str | None = None
    ldapBackupPort: str | None = None
    ldapBackgroundHost: str | None = None
    ldapBackgroundPort: str | None = None
    ldapBase: str
    ldapBaseUsers: str | None = None
    ldapBaseGroups: str | None = None
    ldapAgentName: str
    ldapAgentPassword: str
    ldapTLS: str = "0"
    turnOffCertCheck: str = "0"
    ldapIgnoreNamingRules: str | None = None
    ldapUserDisplayName: str = "cn"
    ldapUserDisplayName2: str | None = None
    ldapUserAvatarRule: str | None = None
    ldapGidNumber: str | None = None
    ldapUserFilterObjectclass: str | None = None
    ldapUserFilterGroups: str | None = None
    ldapUserFilter: str | None = None
    ldapUserFilterMode: str | None = None
    ldapGroupFilter: str | None = None
    ldapGroupFilterMode: str | None = None
    ldapGroupFilterObjectclass: str | None = None
    ldapGroupFilterGroups: str | None = None
    ldapGroupDisplayName: str | None = None
    ldapGroupMemberAssocAttr: str | None = None
    ldapLoginFilter: str = "(&(|(objectclass=person))(uid=%uid))"
    ldapLoginFilterMode: str | None = None
    ldapLoginFilterEmail: str | None = None
    ldapLoginFilterUsername: str | None = None
    ldapLoginFilterAttributes: str | None = None
    ldapQuotaAttribute: str | None = None
    ldapQuotaDefault: str | None = None
    ldapEmailAttribute: str = "mail"
    ldapCacheTTL: str | None = None
    ldapUuidUserAttribute: str | None = None
    ldapUuidGroupAttribute: str | None = None
    ldapOverrideMainServer: str | None = None
    ldapConfigurationActive: str = "1"
    ldapAttributesForUserSearch: str | None = None
    ldapAttributesForGroupSearch: str | None = None
    ldapExperiencedAdmin: str | None = None
    homeFolderNamingRule: str | None = None
    hasMemberOfFilterSupport: str | None = None
    useMemberOfToDetectMembership: str | None = None
    ldapExpertUsernameAttr: str | None = None
    ldapExpertUUIDUserAttr: str | None = None
    ldapExpertUUIDGroupAttr: str | None = None
    markRemnantsAsDisabled: str | None = None
    lastJpegPhotoLookup: str | None = None
    ldapNestedGroups: str | None = None
    ldapPagingSize: str | None = None
    turnOnPasswordChange: str = "1"
    ldapDynamicGroupMemberURL: str | None = None
    ldapDefaultPPolicyDN: str | None = None
    ldapExtStorageHomeAttribute: str | None = None
    ldapMatchingRuleInChainState: str | None = None
    ldapConnectionTimeout: str | None = None
    ldapAttributePhone: str | None = None
    ldapAttributeWebsite: str | None = None
    ldapAttributeAddress: str | None = None
    ldapAttributeTwitter: str | None = None
    ldapAttributeFediverse: str | None = None
    ldapAttributeOrganisation: str | None = None
    ldapAttributeRole: str | None = None
    ldapAttributeHeadline: str | None = None
    ldapAttributeBiography: str | None = None
    ldapAdminGroup: str | None = None
    ldapAttributeBirthDate: str | None = None
    ldapAttributeAnniversaryDate: str | None = None
    ldapAttributePronouns: str | None = None

    @staticmethod
    def from_smarthost_ldap_config(
        smarthost_ldap_config: LdapConfig, base_config: LDAPConfigModel | None = None
    ) -> LDAPConfigModel:
        """Create an instance from a SmartHost ldap config"""
        data = {} if base_config is None else base_config.model_dump(mode="json", exclude_none=True)
        data.update(
            {
                "ldapTLS": str(int(smarthost_ldap_config.tls)),
                "turnOffCertCheckldapHost": str(int(smarthost_ldap_config.tls)),
                "ldapHost": smarthost_ldap_config.hostname,
                "ldapPort": str(smarthost_ldap_config.port),
                "ldapBase": smarthost_ldap_config.base,
                "ldapBaseUsers": smarthost_ldap_config.user_base,
                "ldapBaseGroups": smarthost_ldap_config.groups_base,
                "ldapAgentName": smarthost_ldap_config.service_account_dn,
                "ldapAgentPassword": smarthost_ldap_config.service_account_password,
                "ldapUserFilterObjectclass": smarthost_ldap_config.user_object_class,
                "ldapUserFilter": smarthost_ldap_config.user_filter,
                "ldapGroupFilter": smarthost_ldap_config.group_filter,
                "ldapGroupFilterObjectclass": smarthost_ldap_config.group_object_class,
                "ldapGroupMemberAssocAttr": smarthost_ldap_config.group_member_association_attr,
            }
        )
        return LDAPConfigModel.model_validate(data)
