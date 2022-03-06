from sqlalchemy import Column, Integer, DateTime, String, SmallInteger, Boolean, Text
from sqlalchemy.orm import declared_attr

from app.db.base_class import Base


class SECorrespondence(Base):
    __tablename__ = 'SECorrespondence'
    SeqNo = Column(Integer, primary_key=True)
    DocSentDate = Column(DateTime)
    MailUniqueId = Column(String)
    MailSubject = Column(Text)
    MailBody1 = Column(Text)
    MailTo = Column(Text)
    MailCC = Column(Text)
    MailFrom = Column(Text)
    MailBCC = Column(Text)
    DocSendOn = Column(DateTime)
    DocType = Column(String(10), default='ML')
    QuoteNo = Column(Integer)
    BkgNo = Column(Integer)
    AccountCode = Column(String(10))
    DocumentType = Column(String(10), default='Other')
    IsReceived = Column(Boolean, default=True)
    IsHtmlContent = Column(Boolean, default=True)
    IsAttachmentProcessed = Column(Boolean)
    HasAttachment = Column(Boolean)
    IsHidden = Column(Boolean, default=False)
    FinalInd = Column(Boolean, default=False)
    DocumentSubType = Column(String(20), default='Other')
    IsImport = Column(Boolean, default=True)
    MailPriority = Column(Integer, default=0)
    PublishToMyDhruvInd = Column(Boolean, default=False)
    IsMailSent = Column(Boolean, default=False)
    ConversationId = Column(String(80))
    ConversationId44 = Column(String(44))
    CrUId = Column(String(10), default='AUTO')
    CrDate = Column(DateTime)
    CrTime = Column(DateTime)
    FrzInd = Column(Boolean, default=False)
    UpdUId = Column(String(10), default='AUTO')
    UpdDate = Column(DateTime)
    UpdTime = Column(DateTime)
    UpdPlace = Column(String(10))

