from pydantic import BaseSettings


class Settings(BaseSettings):
    # Logs
    LOG_SERIALIZE = False
    LOG_LEVEL = "DEBUG"
    # App
    HOST = "localhost"
    PORT = 8001
    APP_RELOAD = True
    APP_WORKERS = 1
    API_V1_STR = "v1"
    # Configuration
    CONFIGURATION_PATH = ".."


settings = Settings()
