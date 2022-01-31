import sys

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.api.v1 import api_v1


def create_app():
    # sys.path.append()
    fastapi = FastAPI()
    fastapi.include_router(router=api_v1.router, prefix=f"/{settings.API_V1_STR}")
    return fastapi


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT,
                reload=settings.APP_RELOAD, workers=settings.APP_WORKERS)
