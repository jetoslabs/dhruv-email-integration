from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Correspondence(Base):
    __tablename__ = 'correspondence'
    id = Column(Integer, primary_key=True)
    subject = Column('subject', String(32))
    body = Column('body', String(32))
    attachments = Column('attachments', String(32))
    from_address = Column('from_address', String(32))
    to_address = Column('to_address', String(32))
    # correspondence_id = relationship("CorrespondenceId", uselist=False, back_populates="correspondence")
