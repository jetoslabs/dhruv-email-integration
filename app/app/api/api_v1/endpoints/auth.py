from fastapi import APIRouter

from app.core.auth import get_confidential_client_application, get_access_token
from app.core.config import configuration

router = APIRouter()


@router.get("/token")
def get_token(tenant: str):
    config = configuration.get_ms_auth_config(tenant)
    client_app = get_confidential_client_application(config)
    token = get_access_token(config, client_app)
    return token


@router.get("/callback")
async def callback():
    return "callback"
