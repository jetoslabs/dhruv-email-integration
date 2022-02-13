from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import CorrespondenceId
from app.schemas.schema_db import CorrespondenceIdCreate, CorrespondenceIdUpdate


class CRUDCorrespondenceId(CRUDBase[CorrespondenceId, CorrespondenceIdCreate, CorrespondenceIdUpdate]):

    def create(self, db: Session, *, obj_in: CorrespondenceIdCreate):
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_message_id(self, db: Session, *, message_id: str) -> CorrespondenceId:
        return db.query(self.model).filter(self.model.message_id == message_id).first()

    def get_multi_by_message_id(
            self, db: Session, *, message_id: str, skip: int = 0, limit: int = 0
    ) -> List[CorrespondenceId]:
        return db.query(self.model)\
            .filter(self.model.message_id == message_id)\
            .order_by(message_id)\
            .offset(skip)\
            .limit(limit)\
            .all()
