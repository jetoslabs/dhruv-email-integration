from O365 import Account, FileSystemTokenBackend
from fastapi import FastAPI

from app.api.v1 import api_v1
from app.core.config import settings


def create_app():
    app = FastAPI()
    app.include_router(router=api_v1.v1_router, prefix=f"/{settings.API_V1_STR}")
    return app


app = create_app()

