from typing import List, Any, Optional

from loguru import logger
from sqlalchemy.orm import Session
from app.schemas.schema_sp import EmailTrackerGetEmailIDSchema, EmailTrackerGetEmailLinkInfo, \
    EmailTrackerGetEmailLinkInfoParams


class StoredProcedures:

    @staticmethod
    async def dhruv_EmailTrackerGetEmailID(db_sales97: Session) -> List[EmailTrackerGetEmailIDSchema]:
        res: List[EmailTrackerGetEmailIDSchema] = run_stored_procedure(
            db_sales97, "sales97.dbo.dhruv_EmailTrackerGetEmailID", AnyBaseModelSchema=EmailTrackerGetEmailIDSchema
        )
        return res

    @staticmethod
    async def dhruv_EmailTrackerGetEmailLinkInfo(
            db_fit: Session, param_obj: EmailTrackerGetEmailLinkInfoParams
    ) -> List[EmailTrackerGetEmailLinkInfo]:
        # ordered params list
        params = [param_obj.email, param_obj.empty, param_obj.date]
        res: List[Any] = run_stored_procedure(
            db_fit,
            "fit.dbo.dhruv_EmailTrackerGetEmailLinkInfo",
            params,
            AnyBaseModelSchema=EmailTrackerGetEmailLinkInfo
        )
        return res


def run_stored_procedure(
        db: Session,
        stored_procedure_name: str,
        ordered_params: List[str] = None,
        *,
        AnyBaseModelSchema: type = dict,
) -> List[Any]:
    stored_procedure_name_plus_params = get_stored_procedure_name_plus_params(
        stored_procedure_name, ordered_params
    )
    cursor = db.execute(f"exec {stored_procedure_name_plus_params}")
    result: List[AnyBaseModelSchema] = []
    for row in cursor:
        result.append(AnyBaseModelSchema(**row)) if AnyBaseModelSchema != dict else result.append(row)
    logger.bind(
        stored_procedure_name_plus_params=stored_procedure_name_plus_params,
        result=result[len(result)-1]
    ).debug("Ran Stored procedure")
    return result


def get_stored_procedure_name_plus_params(stored_procedure_name: str, ordered_params: List[str]) -> str:
    stored_procedure_name_plus_params = stored_procedure_name
    if ordered_params is not None:
        params: List[str] = []
        for param in ordered_params:
            params.append(f"'{param}'")
        params_str = ", ".join(params)
        stored_procedure_name_plus_params = f"{stored_procedure_name_plus_params} {params_str}"
    return stored_procedure_name_plus_params
