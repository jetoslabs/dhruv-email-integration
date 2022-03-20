import uvicorn
from fastapi import FastAPI
from loguru import logger

from app.core.config import Config
from app.core.description import description
from app.core.log import setup_logger
from app.core.settings import settings
from app.api.api_v1 import api
from app.middlewares import middleware_tracer


def create_app():
    fastapi = FastAPI(
        title=settings.NAME,
        description=description,
        version=settings.VERSION,
        contact={
            "name": settings.CONTACT_NAME,
            "url": settings.CONTACT_URL,
            "email": settings.CONTACT_EMAIL,
        }
    )

    # Add Router
    fastapi.include_router(router=api.router, prefix=f"/{settings.API_V1_STR}")

    # Add Middleware routers
    fastapi.add_middleware(middleware_tracer.TracerMiddleware)

    return fastapi


app = create_app()


@app.on_event("startup")
async def startup_event():
    # setup logger before everything
    setup_logger()
    logger.bind().info("Startup event")
    # TODO: configuration = Config.validate_and_load(settings.CONFIGURATION_LOC)
    # TODO: setup ConfidentialClientApplication
    # TODO: setup boto3 (s3) session
    # TODO: init here... ms_auth_configs
    # endpoints_ms


@app.on_event("shutdown")
async def shutdown_event():
    logger.bind().info("Shutdown event")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_RELOAD,
        workers=settings.APP_WORKERS
    )
