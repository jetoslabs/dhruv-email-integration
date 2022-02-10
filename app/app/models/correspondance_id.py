from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class CorrespondenceId(Base):
    __tablename__ = 'correspondence_ids'
    id = Column(Integer, primary_key=True)
    message_id = Column('message_id', String(32))
    correspondence = relationship("Correspondence", uselist=False, back_populates="correspondence_id")