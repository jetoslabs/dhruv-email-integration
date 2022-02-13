from sqlalchemy.orm import Session

from app.crud.crud_correspondence_id import CRUDCorrespondenceId
from app.models import CorrespondenceId as CorrespondenceIdModel
from app.schemas.schema_db import CorrespondenceIdCreate as CorrespondenceIdCreateSchema


def test_create_record(db: Session):
    message_id = "okokok"
    correspondence_id_create_schema = CorrespondenceIdCreateSchema(message_id=message_id)
    created = CRUDCorrespondenceId(CorrespondenceIdModel).create(db, obj_in=correspondence_id_create_schema)
    assert created.id != 0 and created.message_id == message_id