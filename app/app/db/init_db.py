from app.db import base

# NOTE: All the tables to be created, first have to be imported in app/db/base.py


def init_db(engine) -> None:
    base.Base.metadata.create_all(engine)
