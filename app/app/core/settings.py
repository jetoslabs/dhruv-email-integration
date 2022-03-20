from pydantic import BaseSettings


class Settings(BaseSettings):
    # Logs
    LOG_SERIALIZE = False
    LOG_LEVEL = "DEBUG"
    ## App
    # FastApi
    NAME = "Dhruv Email Integration"
    VERSION = "0.1.0"
    CONTACT_NAME = "Jetoslabs"
    CONTACT_URL = "https://jetoslabs.com/contact/"
    CONTACT_EMAIL = "toanuragjha@gmail.com"
    # Uvicorn
    HOST = "localhost"
    PORT = 8001
    APP_RELOAD = True
    APP_WORKERS = 1
    API_V1_STR = "v1"
    # Configuration
    CONFIGURATION_PATH = "../"
    CONFIGURATION_LOC = "../configuration"


settings = Settings()
