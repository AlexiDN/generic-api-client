from pydantic import BaseModel, Field

from openstoreplugin.models.application_config import ApplicationConfiguration


class OpenStoreConfigModel(BaseModel):
    # SMARTHOST
    REMOTE_STORE_URL: str = Field("The url of the remote store")
    # HOST
    HOST_USER: str = Field("The user used on the host")
    SERVER_BASE_DOMAIN: str = Field("The base domain of the server (example: test.com)")
    SERVER_PUBLIC_IP: str = Field("The public ip of the server")
    SERVER_PRIVATE_IP: str = Field("The private ip of the server")
    # DOCKER
    VOLUMES_ROOT_DIR: str = Field("The root directory for docker volumes on the host")
    TRAEFIK_CONF: ApplicationConfiguration = Field("The private ip of treafik")
