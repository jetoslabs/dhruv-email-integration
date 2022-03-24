import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def get_sqlalchemy_url(db_name: str) -> str:
    safe_string = urllib.parse.quote_plus(global_config.db_pwd)
    url = global_config.db_url.replace("<db_pwd>", safe_string)
    url = url.replace("<db_name>", db_name)
    return url


def get_db_engine(db_name: str) -> Engine:
    eng = create_engine(url=get_sqlalchemy_url(db_name), pool_pre_ping=True)
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
