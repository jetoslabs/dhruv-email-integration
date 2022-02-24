import json

from loguru import logger
from pydantic import BaseModel, Field
from typing import Dict, Optional

from app.core.settings import settings


class OptionalQueryParams(BaseModel):
    top: Optional[str] = Field(None, alias="$top")
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


class MsEndpointHelper:
    @staticmethod
    def form_url(endpoint: MsEndpoint):
        result_url = "" + endpoints_ms.base_url + endpoint.request_path_template
        if endpoint.request_params:
            for param_name, param_value in endpoint.request_params.items():
                result_url = result_url.replace("{"+param_name+"}", param_value)
        if endpoint.optional_query_params:
            for param_name, param_value in endpoint.optional_query_params.dict().items():
                if param_value and '<' not in param_value and '>' not in param_value:
                    result_url = f"{result_url}?{param_name}={param_value}"
        return result_url


class MsEndpointsHelper:
    @staticmethod
    def _load_endpoints_ms(filepath: str) -> MsEndpoints:
        try:
            with open(filepath) as file:
                data = json.load(file)
            return MsEndpoints(**data)
        except FileNotFoundError as e:
            logger.bind(filepath=filepath).error("cannot load endpoint_ms")
            raise e
        except Exception as e:
            logger.bind(filepath=filepath).error("cannot load endpoint_ms")
            raise e

    @staticmethod
    def get_endpoint(endpoint_name: str, ms_endpoints: MsEndpoints) -> MsEndpoint:
        return ms_endpoints.endpoints.get(endpoint_name).copy()

    # @staticmethod
    # def form_url(endpoint_name: str, endpoints_ms: MsEndpoints) -> str:
    #     endpoint = MsEndpointsHelper.get_endpoint(endpoint_name, endpoints_ms)
    #     result_url = endpoints_ms.base_url + MSEndpointHelper.form_url(endpoint.request_url, endpoint.request_params)
    #     return result_url


# endpoints_ms # TODO: move
# endpoints_ms: MsEndpoints = MsEndpointsHelper._load_endpoints_ms("../configuration/endpoints_ms.json")
endpoints_ms: MsEndpoints = MsEndpointsHelper._load_endpoints_ms(f"{settings.CONFIGURATION_PATH}configuration/endpoints_ms.json")
