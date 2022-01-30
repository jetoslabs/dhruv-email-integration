from O365 import Account, FileSystemTokenBackend
from fastapi import FastAPI

from app.api.v1 import api_v1


def create_app():
    app = FastAPI()
    app.include_router(api_v1.v1_router)
    return app


app = create_app()

