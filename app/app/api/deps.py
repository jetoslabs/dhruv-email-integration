import json
from typing import Generator

from app.core.auth import MsAuthConfig, get_confidential_client_application, get_access_token
from app.db.db_session import SessionLocal


def get_token(tenant: str):
    config_dict = json.load(open('../configuration/ms_auth_configs.json'))[tenant]
    config = MsAuthConfig(**config_dict)
    client_app = get_confidential_client_application(config)
    token = get_access_token(config, client_app)
    return token


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
