from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.db.base_class import Base


class SimpleSchema(BaseModel):
    id: Optional[int]
    message_id: Optional[str]


class SimpleModel(Base):
    id = Column(Integer, primary_key=True)
    message_id = Column('message_id', String(32))


def test_create_record(db: Session):
    message_id = "ok_ok_ok"
    base_schema = SimpleSchema(message_id=message_id)
    created = CRUDBase(SimpleModel).create(db, obj_in=base_schema)
    assert created.id != 0 and created.message_id == message_id


def test_get_multi(db: Session):
    message_id = "ok_ok_ok"
    base_schema = SimpleSchema(message_id=message_id)
    CRUDBase(SimpleModel).create(db, obj_in=base_schema)
    result = CRUDBase(SimpleModel).get_multi(db=db)
    assert len(result) >= 1


def test_update(db: Session):
    message_id = "ok_ok_ok1"
    updated_message_id = "ko_ko_ko1"
    created = CRUDBase(SimpleModel).create(db, obj_in=SimpleSchema(message_id=message_id))
    assert created.message_id == message_id
    updated = CRUDBase(SimpleModel).update(db, db_obj=created, obj_in=SimpleSchema(message_id=updated_message_id))
    assert updated.message_id == updated_message_id


def test_exists(db: Session):
    # does not exist
    is_exist = CRUDBase(SimpleModel).exists(db, id=1231123)
    assert not is_exist

    # does exist
    message_id = "ok_ok_ok"
    base_schema = SimpleSchema(message_id=message_id)
    created = CRUDBase(SimpleModel).create(db, obj_in=base_schema)
    is_exist = CRUDBase(SimpleModel).exists(db, id=created.id)
    assert is_exist
