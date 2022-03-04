from typing import Any

from app.apiclients.api_client import ApiClient
from app.apiclients.endpoint_ms import MsEndpointsHelper, endpoints_ms, MsEndpointHelper
from app.schemas.schema_ms_graph import UsersSchema


class UsersController:

    @staticmethod
    async def get_users(token: Any, top: int, select: str, filter: str) -> UsersSchema:
        # ms graph api - https://docs.microsoft.com/en-us/graph/api/user-list?view=graph-rest-1.0&tabs=http
        endpoint = MsEndpointsHelper.get_endpoint("user:list", endpoints_ms)
        if top >= 0 or top <= 1000: endpoint.optional_query_params.top = top
        endpoint.optional_query_params.select = select
        endpoint.optional_query_params.filter = filter
        # We can get url from endpoint as is. This is because this endpoint url is simple get
        url = MsEndpointHelper.form_url(endpoint)
        response, data = await ApiClient('get', url, headers=ApiClient.get_headers(token)).retryable_call()
        return UsersSchema(**data) if type(data) == 'dict' else data
