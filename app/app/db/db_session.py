import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import configuration


def get_tenant_sqlalchemy_url(tenant: str, db_name: str) -> str:
    safe_string_pwd = urllib.parse.quote_plus(configuration.tenant_configurations.get(tenant).db.db_pwd)
    url = configuration.tenant_configurations.get(tenant).db.db_url.replace("<db_pwd>", safe_string_pwd)
    url = url.replace("<db_name>", db_name)
    return url


def get_tenant_db_engine(tenant: str, db_name: str) -> Engine:
    eng = create_engine(url=get_tenant_sqlalchemy_url(tenant, db_name), pool_pre_ping=True)
    return eng


def get_db_session(eng: Engine):
    session_local = sessionmaker(bind=eng)
    return session_local


# create an engine
# engine = create_engine(get_sqlalchemy_url(global_config.db_sales97_name), pool_pre_ping=True)

# create a configured "Session" class
# SessionLocal = sessionmaker(bind=engine)

# create a Session
# db_session = SessionLocal()
# db_session.connection()
