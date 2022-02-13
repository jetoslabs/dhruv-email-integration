from pydantic import BaseModel


class CorrespondenceId(BaseModel):
    message_id: str


class CorrespondenceIdCreate(CorrespondenceId):
    pass


class CorrespondenceIdUpdate(CorrespondenceId):
    pass


class Correspondence(BaseModel):
    subject: str
    body: str
    attachments: str
    from_address: str
    to_address: str


class CorrespondenceCreate(Correspondence):
    pass


class CorrespondenceUpdate(Correspondence):
    pass
