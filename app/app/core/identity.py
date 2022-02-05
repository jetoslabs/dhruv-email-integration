#  MS Identity Platform
import json
from typing import Any, Union, Tuple, Dict

import msal
from loguru import logger
from msal import ConfidentialClientApplication
from pydantic import BaseModel


class Config(BaseModel):
    authority: str
    client_id: str
    scope: list
    secret: str
    endpoint: str


def get_config(tenant) -> Config:
    config_dict: dict = json.load(open('../parameters.json'))
    config_dict = config_dict.get(tenant)
    config = Config(**config_dict)
    return config


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


def get_access_token(config: Config, app: ConfidentialClientApplication):
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


def get_config_and_confidential_client_application_and_access_token(tenant) -> Union[
    tuple[Config, ConfidentialClientApplication, Any], tuple[None, None, None]]:
    config = get_config(tenant)
    if config is not None:
        client_app = get_confidential_client_application(config)
        token = get_access_token(config, client_app)
        return config, client_app, token
    return config, None, None