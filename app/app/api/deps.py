import json

from app.core.auth import MsAuthConfig, get_confidential_client_application, get_access_token


def get_token(tenant: str):
    config_dict = json.load(open('../configuration/ms_auth_configs.json'))[tenant]
    config = MsAuthConfig(**config_dict)
    client_app = get_confidential_client_application(config)
    token = get_access_token(config, client_app)
    return token
