from fastapi import APIRouter

from app.apiclients.api_client import ApiClient
from app.apiclients.endpoint_ms import endpoints_ms, MsEndpointsHelper, MsEndpointHelper
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.schemas.schema_ms_graph import UsersSchema, UserResponseSchema

router = APIRouter()


@router.get("/users/", response_model=UsersSchema)
async def get_users(tenant: str) -> UsersSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        # ms graph api - https://docs.microsoft.com/en-us/graph/api/user-list?view=graph-rest-1.0&tabs=http
        endpoint = MsEndpointsHelper.get_endpoint("user:list", endpoints_ms)
        # We can get url from endpoint as is. This is because this endpoint url is simple get
        url = MsEndpointHelper.form_url(endpoint)
        response, data = await ApiClient('get', url, headers=ApiClient.get_headers(token)).retryable_call()
        return UsersSchema(**data) if type(data) == 'dict' else data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


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
