from typing import List, Optional

from fastapi.encoders import jsonable_encoder
from loguru import logger
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Correspondence
from app.schemas.schema_db import CorrespondenceCreate, CorrespondenceUpdate


class CRUDCorrespondence(CRUDBase[Correspondence, CorrespondenceCreate, CorrespondenceUpdate]):

    def create(self, db: Session, *, obj_in: CorrespondenceCreate) -> Correspondence:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.bind().debug("")
        return db_obj

    def get_by_message_id(self, db: Session, *, message_id: str) -> Optional[Correspondence]:
        return db.query(self.model).filter(self.model.message_id == message_id).first()

    def get_by_message_id_or_create_get_if_not_exist(self, db: Session, *, obj_in: CorrespondenceCreate) -> Optional[Correspondence]:
        db_obj = self.get_by_message_id(db, message_id=obj_in.message_id)
        if db_obj is None:
            db_obj = self.create(db, obj_in=obj_in)
        return db_obj

    def get_by_message_id_or_create_get_if_not_exist_multi(self, db: Session, *, obj_ins: List[CorrespondenceCreate]) -> List[Correspondence]:
        db_objs: List[Correspondence] = []
        for obj_in in obj_ins:
            db_obj = self.get_by_message_id_or_create_get_if_not_exist(db, obj_in=obj_in)
            if db_obj is not None:
                db_objs.append(db_obj)
        return db_objs

    def get_multi_by_message_id(
            self, db: Session, *, message_id: str, skip: int = 0, limit: int = 0
    ) -> List[Correspondence]:
        return db.query(self.model) \
            .filter(self.model.message_id == message_id) \
            .order_by(message_id) \
            .offset(skip) \
            .limit(limit) \
            .all()
