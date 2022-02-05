import uvicorn
from fastapi import FastAPI
from loguru import logger

from app.core.log import setup_logger
from app.core.setting import settings
from app.api.v1 import api_v1


def create_app():
    fastapi = FastAPI()
    fastapi.include_router(router=api_v1.router, prefix=f"/{settings.API_V1_STR}")
    return fastapi


app = create_app()


@app.on_event("startup")
async def startup_event():
    logger.bind().info("startup event ...")
    # setup logger before everything
    setup_logger()
    # TODO: setup ConfidentialClientApplication
    # TODO: setup boto3 (s3) session


@app.on_event("shutdown")
async def shutdown_event():
    logger.bind().info("shutdown event ...")

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT,
                reload=settings.APP_RELOAD, workers=settings.APP_WORKERS)