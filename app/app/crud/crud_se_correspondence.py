from typing import Optional, List

from fastapi.encoders import jsonable_encoder
from loguru import logger
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.se_correspondence import SECorrespondence
from app.schemas.schema_db import SECorrespondenceCreate, SECorrespondenceUpdate


class CRUDSECorrespondence(CRUDBase[SECorrespondence, SECorrespondenceCreate, SECorrespondenceUpdate]):

    def create(self, db: Session, *, obj_in: SECorrespondenceCreate):
        logger.bind(obj_in=obj_in).info("Creating row in SECorrespondence")
        try:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            logger.error(e)

    def get_by_mail_unique_id(self, db: Session, *, mail_unique_id: str) -> Optional[SECorrespondence]:
        return db.query(self.model).filter(self.model.MailUniqueId == mail_unique_id).first()

    def get_where_conversation_id_44_is_empty(self, db: Session, *, skip: int = 0, limit: int = 100) -> Optional[SECorrespondence]:
        return db.query(self.model).with_entities(self.model.SeqNo, self.model.MailUniqueId, self.model.ConversationId, self.model.ConversationId44).where(self.model.MailUniqueId != "").filter(
            self.model.ConversationId44 == None).order_by(self.model.SeqNo.desc()).offset(skip).limit(limit).all()

    def get_by_mail_unique_id_or_create_get_if_not_exist(self, db: Session, *, obj_in: SECorrespondenceCreate) -> Optional[SECorrespondence]:
        db_obj = self.get_by_mail_unique_id(db, mail_unique_id=obj_in.MailUniqueId)
        if db_obj is None:
            db_obj = self.create(db, obj_in=obj_in)
        return db_obj

    def get_by_mail_unique_id_or_create_get_if_not_exist_multi(self, db: Session, *, obj_ins: List[SECorrespondenceCreate]) -> List[SECorrespondence]:
        db_objs: List[SECorrespondence] = []
        for obj_in in obj_ins:
            db_obj = self.get_by_mail_unique_id_or_create_get_if_not_exist(db, obj_in=obj_in)
            if db_obj is not None:
                db_objs.append(db_obj)
        return db_objs
