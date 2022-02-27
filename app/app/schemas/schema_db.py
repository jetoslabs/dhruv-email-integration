import datetime

from pydantic import BaseModel


class SECorrespondence(BaseModel):
    DocSentDate: datetime.datetime
    MailUniqueId: str
    MailSubject: str
    MailBody1: str
    MailTo: str
    MailCC: str
    MailFrom: str
    MailBCC: str
    DocSendOn: datetime.datetime
    QuoteNo: int
    BkgNo: int
    AccountCode: str
    IsAttachmentProcessed: bool
    HasAttachment: bool


class SECorrespondenceCreate(SECorrespondence):
    pass


class SECorrespondenceUpdate(BaseModel):
    IsAttachmentProcessed: bool


class CorrespondenceId(BaseModel):
    message_id: str


class CorrespondenceIdCreate(CorrespondenceId):
    pass


class CorrespondenceIdUpdate(CorrespondenceId):
    pass


class Correspondence(BaseModel):
    message_id: str
    subject: str
    body: str
    attachments: str
    from_address: str
    to_address: str


class CorrespondenceCreate(Correspondence):
    pass


class CorrespondenceUpdate(Correspondence):
    pass

