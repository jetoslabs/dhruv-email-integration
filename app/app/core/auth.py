#  MS Identity Platform
import json
import sys
from typing import Any, Union, Tuple, Dict, Optional

import msal
from loguru import logger
from msal import ConfidentialClientApplication
from pydantic import BaseModel

from app.core.settings import settings


class MsAuthConfig(BaseModel):
    authority: str
    client_id: str
    scope: list
    secret: str
    internal_domains: Optional[list]
    endpoint: str


class MsAuthConfigs(BaseModel):
    configs: Dict[str, MsAuthConfig]


def load_ms_auth_configs(filepath: str) -> MsAuthConfigs:
    try:
        configs_dict: dict = json.load(open(filepath))
        configs = MsAuthConfigs(**configs_dict)
        return configs
    except Exception as e:
        logger.bind(error=e, filepath=filepath).error(f"Error while loading ms_auth_configs, filepath = {filepath}... Exiting\n {e}")
        sys.exit(1)


def get_ms_auth_config(tenant: str) -> MsAuthConfig:
    config = ms_auth_configs.configs[tenant]
    return config


# def is_email_in_internal_domains(tenant: str, email: str) -> bool:
#     tenant_auth_config = get_ms_auth_config(tenant)
#     internal_domains: Optional[list] = tenant_auth_config.internal_domains
#     if internal_domains is None: return False
#     return email in internal_domains


# TODO: move var - this is one of the many vars for global store
# ms_auth_configs = load_ms_auth_configs("../configuration/ms_auth_configs.json")
ms_auth_configs = load_ms_auth_configs(f"{settings.CONFIGURATION_PATH}configuration/ms_auth_configs.json")


def get_confidential_client_application(config) -> ConfidentialClientApplication:
    # TODO: make ConfidentialClientApplication long-lived (should be 1 for each tenant)
    # Create a preferably long-lived app instance which maintains a token cache.
    app: ConfidentialClientApplication = msal.ConfidentialClientApplication(
        config.client_id,
        authority=config.authority,
        client_credential=config.secret,
        # token_cache=...  # Default cache is in memory only.
        # You can learn how to use SerializableTokenCache from
        # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
    )
    return app


def get_access_token(config: MsAuthConfig, app: ConfidentialClientApplication):
    # The pattern to acquire a token looks like this.
    result = None

    # Firstly, looks up a token from cache
    # Since we are looking for token for the current app, NOT for an end user,
    # notice we give account parameter as None.
    result = app.acquire_token_silent(config.scope, account=None)

    if not result:
        logger.info("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=config.scope)

    return result


def get_auth_config_and_confidential_client_application_and_access_token(tenant) -> Union[
    Tuple[MsAuthConfig, ConfidentialClientApplication, Any], Tuple[None, None, None]]:
    config = get_ms_auth_config(tenant)
    if config is not None:
        client_app = get_confidential_client_application(config)
        token = get_access_token(config, client_app)
        return config, client_app, token
    return config, None, None
