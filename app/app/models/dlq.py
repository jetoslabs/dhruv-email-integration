from sqlalchemy import Column, Integer, String


from app.db.base_class import Base


class DLQ(Base):
    __tablename__ = 'dlq'
    id = Column(Integer, primary_key=True)
    error = Column('error', String)
    data = Column('data', String)
    
