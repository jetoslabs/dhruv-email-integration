from pydantic import BaseModel


class EmailTrackerGetEmailIDSchema(BaseModel):
    UserName: str
    EMailId: str
    UserCode: str


class EmailTrackerGetEmailLinkInfoParams(BaseModel):
    email: str
    empty: str = ''
    date: str
    conversation_id_44: str


class EmailTrackerGetEmailLinkInfo(BaseModel):
    AccountCode: str
    QuoteNo: int
    BkgNo: int
