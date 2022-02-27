from app.crud.base import CRUDBase
from app.models.se_correspondence import SECorrespondence
from app.schemas.schema_db import SECorrespondenceCreate, SECorrespondenceUpdate


class CRUDSECorrespondence(CRUDBase[SECorrespondence, SECorrespondenceCreate, SECorrespondenceUpdate]):
    pass