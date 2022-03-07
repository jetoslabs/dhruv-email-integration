from typing import Optional

from fastapi import APIRouter, HTTPException

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
        user_schema = await UserController.get_user(token, user_id)
        return user_schema
    else:
        raise_http_exception(token, 401, "Unauthorized")


@router.get("/users/emails/{user_email}", response_model=UserSchema)
async def get_user_by_email(tenant: str, user_email: str) -> Optional[UserSchema]:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        user: Optional[UserSchema] = await UserController.get_user_by_email(token, user_email, "")
        if user is None:
            raise HTTPException(status_code=404)
        return user
    else:
        raise_http_exception(token, 401, "Unauthorized")
