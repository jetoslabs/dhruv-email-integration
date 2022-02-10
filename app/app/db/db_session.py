from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import global_config

# create an engine
engine = create_engine(global_config.db_url, pool_pre_ping=True)

# create a configured "Session" class
Session = sessionmaker(bind=engine)

# create a Session
db_session = Session()
db_session.connection()