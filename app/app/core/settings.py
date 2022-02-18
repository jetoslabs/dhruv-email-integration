from pydantic import BaseSettings


class Settings(BaseSettings):
    LOG_SERIALIZE = False
    LOG_LEVEL = "DEBUG"
    HOST = "localhost"
    PORT = 8001
    APP_RELOAD = True
    APP_WORKERS = 1
    API_V1_STR = "v1"


settings = Settings()
