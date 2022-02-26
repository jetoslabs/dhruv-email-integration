from typing import List, Optional

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

    def get_by_message_id(self, db: Session, *, message_id: str) -> Optional[CorrespondenceId]:
        return db.query(self.model).filter(self.model.message_id == message_id).first()

    def get_by_message_id_or_create_if_not_exist(self, db: Session, *, obj_in: CorrespondenceIdCreate) -> Optional[CorrespondenceId]:
        correspondence_id: Optional[CorrespondenceId] = self.get_by_message_id(db, message_id=obj_in.message_id)
        if correspondence_id is None:
            correspondence_id = self.create(db, obj_in=obj_in)
        return correspondence_id

    def get_by_message_id_or_create_if_not_exist_multi(self, db: Session, *, obj_ins: List[CorrespondenceIdCreate]) -> List[CorrespondenceId]:
        db_objs: List[CorrespondenceId] = []
        for obj_in in obj_ins:
            db_obj = self.get_by_message_id_or_create_if_not_exist(db, obj_in=obj_in)
            if db_obj is not None:
                db_objs.append(db_obj)
        return db_objs

    def get_multi_by_message_id(
            self, db: Session, *, message_id: str, skip: int = 0, limit: int = 0
    ) -> List[CorrespondenceId]:
        return db.query(self.model)\
            .filter(self.model.message_id == message_id)\
            .order_by(message_id)\
            .offset(skip)\
            .limit(limit)\
            .all()
