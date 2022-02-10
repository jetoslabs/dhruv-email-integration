# Import all the models, so that Base has them before being
# imported by Alembic


# NOTE: This file will import base_class from this app.db package, and rest of the models from app.models package
from app.db.base_class import Base  # noqa
from app.models.correspondance_id import CorrespondenceId  # noqa
from app.models.correspondance import Correspondence  # noqa