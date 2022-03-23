from typing import Any, Optional, List

from loguru import logger
from sqlalchemy.orm import Session

from app.apiclients.api_client import ApiClient
from app.apiclients.endpoint_ms import MsEndpointsHelper, endpoints_ms, MsEndpointHelper
from app.crud.stored_procedures import StoredProcedures
from app.schemas.schema_ms_graph import UsersSchema, UserSchema, UserResponseSchema
from app.schemas.schema_sp import EmailTrackerGetEmailIDSchema


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
        return UserResponseSchema(**data)# if type(data) == 'dict' else None

    @staticmethod
    async def get_user_by_email(token: Any, user_email: str, select: str) -> Optional[UserSchema]:
        endpoint = MsEndpointsHelper.get_endpoint("user:list", endpoints_ms)
        endpoint.optional_query_params.top = 5
        endpoint.optional_query_params.select = select
        endpoint.optional_query_params.filter = f"mail eq '{user_email}'"
        url = MsEndpointHelper.form_url(endpoint)
        response, data = await ApiClient('get', url, headers=ApiClient.get_headers(token)).retryable_call()
        if data is None or "value" not in data or len(data["value"]) == 0:
            logger.bind(user_email=user_email, data=data).debug("Empty response for user list from msgraph")
            return None
        users = UsersSchema(**data)
        try:
            return users.value[0]
        except Exception as e:
            logger.bind().error(e)

    @staticmethod
    async def get_users_to_track(
            token: Any,
            db_sales97: Session,
    ) -> List[UserSchema]:
        # get list of trackable users
        users_to_track: List[EmailTrackerGetEmailIDSchema] = \
            await StoredProcedures.dhruv_EmailTrackerGetEmailID(db_sales97)
        # get user ids for those email ids
        users: List[UserSchema] = []
        for user_to_track in users_to_track:
            user = await UserController.get_user_by_email(token, user_to_track.EMailId, "")
            if user is None:
                logger.bind(user_to_track=user_to_track).error("Cannot find in Azure")
            else:
                logger.bind(user_to_track=user_to_track).debug("Found in Azure")
                users.append(user)
        return users
