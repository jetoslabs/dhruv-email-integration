import json
from typing import Generator

from app.core.auth import MsAuthConfig, get_confidential_client_application, get_access_token
from app.core.config import global_config
from app.db.db_session import SessionLocal, get_db_engine, get_db_session


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


def get_sales97_db() -> Generator:
    try:
        session_local = get_db_session(get_db_engine(global_config.db_sales97_name))
        db = session_local()
        yield db
    finally:
        db.close()


def get_fit_db() -> Generator:
    try:
        session_local = get_db_session(get_db_engine(global_config.db_fit_name))
        db = session_local()
        yield db
    finally:
        db.close()


def get_mailstore_db() -> Generator:
    try:
        session_local = get_db_session(get_db_engine(global_config.db_mailstore_name))
        db = session_local()
        yield db
    finally:
        db.close()
