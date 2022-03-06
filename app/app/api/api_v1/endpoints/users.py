from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.apiclients.api_client import ApiClient
from app.apiclients.endpoint_ms import endpoints_ms, MsEndpointsHelper, MsEndpointHelper
from app.controllers.common import raise_http_exception
from app.controllers.user import UserController
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.schemas.schema_ms_graph import UsersSchema, UserResponseSchema, UserSchema

router = APIRouter()


@router.get("/users/", response_model=UsersSchema)
async def get_users(tenant: str, top: int = 5, select: str = "", filter: str = "") -> UsersSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        users_schema = await UserController.get_users(token, top, select, filter)
        return users_schema
    else:
        raise_http_exception(token, 401, "Unauthorized")


@router.get("/users/{user_id}", response_model=UserResponseSchema)
async def get_user(tenant: str, user_id: str) -> UserResponseSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        # ms graph api - https://docs.microsoft.com/en-us/graph/api/user-get?view=graph-rest-1.0&tabs=http
        endpoint = MsEndpointsHelper.get_endpoint("user:get", endpoints_ms)
        # update the endpoint request_params
        endpoint.request_params["user_id"] = user_id
        url = MsEndpointHelper.form_url(endpoint)
        response, data = await ApiClient('get', url, headers=ApiClient.get_headers(token)).retryable_call()
        return UserResponseSchema(**data) if type(data) == 'dict' else data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/users/{user_email}", response_model=UserSchema)
async def get_user_by_email(tenant: str, user_email: str) -> Optional[UserSchema]:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        user: Optional[UserSchema] = await UserController.get_user_by_email(token, user_email, "")
        if user is None:
            raise HTTPException(status_code=404)
        return user
    else:
        raise_http_exception(token, 401, "Unauthorized")
