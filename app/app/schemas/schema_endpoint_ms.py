from typing import Optional, Dict

from pydantic import BaseModel, Field


class OptionalQueryParams(BaseModel):
    top: Optional[str] = Field(None, alias="$top")
    select: Optional[str] = Field(None, alias="$select")
    filter: Optional[str] = Field(None, alias="$filter")
    orderby: Optional[str] = Field(None, alias="$orderby")


class MsEndpoint(BaseModel):
    application_permissions: list
    request_method: str
    request_path_template: str
    request_params: dict
    optional_query_params: Optional[OptionalQueryParams]


class MsEndpoints(BaseModel):
    base_url: str
    endpoints: Dict[str, MsEndpoint]