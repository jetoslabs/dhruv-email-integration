from typing import Generator

import pytest

from app.db.base_class import Base
from app.db.db_session import engine, db_session


@pytest.fixture(scope="session")
def db() -> Generator:
    db = db_session
    Base.metadata.create_all(engine)
    yield db
