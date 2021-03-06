from typing import TypeVar, Generic, Type, Any, Optional, List, Union, Dict

from fastapi.encoders import jsonable_encoder
from loguru import logger
from pydantic import BaseModel

from app.db.base_class import Base
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, seq_no: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.SeqNo == seq_no).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).order_by(self.model.SeqNo).offset(skip).limit(limit).all()

    def exists(self, db: Session, *, SeqNo: Any) -> bool:
        return db.query(SeqNo).filter(self.model.id == SeqNo).first() is not None

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_multi(self, db: Session, *, obj_ins: List[CreateSchemaType]) -> List[ModelType]:
        db_objs: List[ModelType] = []
        for obj_in in obj_ins:
            try:
                db_obj = self.create(db, obj_in=obj_in)
                db_objs.append(db_obj)
            except Exception as e:
                logger.bind(obj_in=obj_in).error("Cannot create")
        return db_objs

    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, seq_no: int) -> ModelType:
        obj = db.query(self.model).get(seq_no)
        db.delete(obj)
        db.commit()
        return obj
