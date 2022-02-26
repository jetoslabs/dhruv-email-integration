from sqlalchemy.orm import Session

from app.controllers.mail import get_s3_path_from_ms_message_id, get_attachments_path_from_id


def test_get_s3_path_from_correspondence_id():
    dir_str = get_attachments_path_from_id(id=1, min_length=6)
    assert dir_str == "0/0/0/0/0/1"


def test_get_s3_path_from_ms_message_id(db: Session):
    path = get_s3_path_from_ms_message_id(db, "1")
    assert path == "0/0/0/0/0/1"
