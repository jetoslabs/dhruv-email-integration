from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Correspondence(Base):
    __tablename__ = 'correspondence'
    id = Column(Integer, primary_key=True)
    message_id = Column('message_id', String)
    subject = Column('subject', String)
    body = Column('body', String)
    attachments = Column('attachments', String)
    from_address = Column('from_address', String)
    to_address = Column('to_address', String)
    # correspondence_id = relationship("CorrespondenceId", uselist=False, back_populates="correspondence")
