from sqlalchemy.orm import Session

from app.controllers.mail import get_attachments_path_from_id


def test_get_s3_path_from_correspondence_id():
    dir_str = get_attachments_path_from_id(id=1, min_length=6)
    assert dir_str == "0/0/0/0/0/1/1"

    path = get_attachments_path_from_id(id=93245233)
    assert path == "9/3/2/4/5/2/3/3/93245233"
