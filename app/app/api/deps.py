import json
from typing import Generator

from fastapi import HTTPException
from fastapi.responses import Response

from app.core.auth import get_confidential_client_application, get_access_token
from app.core.config import configuration, AzureAuth
from app.db.db_session import get_db_engine, get_db_session


def assert_tenant(tenant: str) -> bool:
    tenant_config = configuration.tenant_configurations.get(tenant)
    if tenant_config is None:
        raise HTTPException(status_code=401)
    return True

def get_token(tenant: str):
    # config_dict = json.load(open('../configuration/ms_auth_configs.json'))[tenant]
    # config = MsAuthConfig(**config_dict)
    # client_app = get_confidential_client_application(config)

    tenant_azure_auth: AzureAuth = configuration.tenant_configurations.get(tenant).azure_auth
    client_app = get_confidential_client_application(tenant_azure_auth)
    token = get_access_token(tenant_azure_auth, client_app)
    return token


def get_tenant_fit_db(tenant: str) -> Generator:
    try:
        session_local = get_db_session(get_db_engine(configuration.tenant_configurations.get(tenant).db.db_fit_name))
        db = session_local()
        yield db
    finally:
        db.close()


def get_tenant_sales97_db(tenant: str) -> Generator:
    try:
        session_local = get_db_session(get_db_engine(configuration.tenant_configurations.get(tenant).db.db_sales97_name))
        db = session_local()
        yield db
    finally:
        db.close()


def get_tenant_mailstore_db(tenant: str) -> Generator:
    try:
        session_local = get_db_session(get_db_engine(configuration.tenant_configurations.get(tenant).db.db_mailstore_name))
        db = session_local()
        yield db
    finally:
        db.close()


# def get_db() -> Generator:
#     try:
#         db = SessionLocal()
#         yield db
#     finally:
#         db.close()


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
