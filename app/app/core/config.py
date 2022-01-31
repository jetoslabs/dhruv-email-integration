from pydantic import BaseSettings


class Settings(BaseSettings):
    HOST = "localhost"
    PORT = 8001
    APP_RELOAD = True
    APP_WORKERS = 2
    API_V1_STR = "v1"


settings = Settings()
