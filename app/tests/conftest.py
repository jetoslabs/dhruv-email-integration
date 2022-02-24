from typing import Generator

import pytest

from app.db.base_class import Base
from app.db.db_session import engine, SessionLocal


@pytest.fixture(scope="session")
def db() -> Generator:
    db = SessionLocal()
    Base.metadata.create_all(engine)
    yield db
