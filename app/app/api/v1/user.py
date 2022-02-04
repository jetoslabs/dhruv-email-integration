from fastapi import APIRouter

from app.api.endpoint import Endpoint
from app.apiclients.api_client import ApiClient
from app.core.identity import get_config_and_confidential_client_application_and_access_token

router = APIRouter()


@router.get("/")
async def get_users(tenant: str):
    config, client_app, token = get_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        response, data = await ApiClient('get', Endpoint.users.value, headers=ApiClient.get_headers(token)).retryable_call()
        return data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug
