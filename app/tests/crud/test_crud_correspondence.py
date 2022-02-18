from sqlalchemy.orm import Session

from app.crud.crud_correspondence import CRUDCorrespondence
from app.models import Correspondence
from app.schemas.schema_db import CorrespondenceCreate


def test_create_record(db: Session):
    correspondence_create_schema = CorrespondenceCreate(
        message_id="message_id",
        subject="subject",
        body="body",
        attachments="links to attachment",
        from_address="from addresses",
        to_address="to addresses"
    )
    created = CRUDCorrespondence(Correspondence).create(db, obj_in=correspondence_create_schema)
    assert created.id != 0 and created.message_id == correspondence_create_schema.message_id
