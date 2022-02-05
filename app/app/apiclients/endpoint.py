import json

from loguru import logger
from pydantic import BaseModel


class MsEndpoint(BaseModel):
    application_permissions: list
    request_method: str
    request_url: str
    request_params: dict


class MSEndpoints(BaseModel):
    base_url: str = "https://graph.microsoft.com/v1.0"
    endpoints: dict[str, MsEndpoint]


class MsEndpointsHelper:
    @staticmethod
    async def load_endpoints_ms(filepath: str):
        try:
            with open(filepath) as file:
                data = json.load(file)
            return data
        except FileNotFoundError as e:
            logger.bind(filepath=filepath).error("cannot load endpoint_ms")
            raise e

    # @staticmethod
    # async def
