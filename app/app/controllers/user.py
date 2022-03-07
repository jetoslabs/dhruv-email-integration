from typing import Any, Optional

from loguru import logger

from app.apiclients.api_client import ApiClient
from app.apiclients.endpoint_ms import MsEndpointsHelper, endpoints_ms, MsEndpointHelper
from app.schemas.schema_ms_graph import UsersSchema, UserSchema, UserResponseSchema


class UserController:

    @staticmethod
    async def get_users(token: Any, top: int, select: str, filter: str) -> Optional[UsersSchema]:
        # ms graph api - https://docs.microsoft.com/en-us/graph/api/user-list?view=graph-rest-1.0&tabs=http
        endpoint = MsEndpointsHelper.get_endpoint("user:list", endpoints_ms)
        if top >= 0 or top <= 1000: endpoint.optional_query_params.top = top
        endpoint.optional_query_params.select = select
        endpoint.optional_query_params.filter = filter
        # We can get url from endpoint as is. This is because this endpoint url is simple get
        url = MsEndpointHelper.form_url(endpoint)
        response, data = await ApiClient('get', url, headers=ApiClient.get_headers(token)).retryable_call()
        if data is None: return None
        users = UsersSchema(**data)
        return users

    @staticmethod
    async def get_user(token: Any, user_id: str) -> Optional[UserResponseSchema]:
        # ms graph api - https://docs.microsoft.com/en-us/graph/api/user-get?view=graph-rest-1.0&tabs=http
        endpoint = MsEndpointsHelper.get_endpoint("user:get", endpoints_ms)
        # update the endpoint request_params
        endpoint.request_params["user_id"] = user_id
        url = MsEndpointHelper.form_url(endpoint)
        response, data = await ApiClient('get', url, headers=ApiClient.get_headers(token)).retryable_call()
        return UserResponseSchema(**data) if type(data) == 'dict' else None

    @staticmethod
    async def get_user_by_email(token: Any, user_email: str, select: str) -> Optional[UserSchema]:
        endpoint = MsEndpointsHelper.get_endpoint("user:list", endpoints_ms)
        endpoint.optional_query_params.top = 5
        endpoint.optional_query_params.select = select
        endpoint.optional_query_params.filter = f"mail eq '{user_email}'"
        url = MsEndpointHelper.form_url(endpoint)
        response, data = await ApiClient('get', url, headers=ApiClient.get_headers(token)).retryable_call()
        if data is None or len(data["value"]) == 0: return None
        users = UsersSchema(**data)
        try:
            return users.value[0]
        except Exception as e:
            logger.bind().error(e)
