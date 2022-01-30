from pydantic import BaseSettings


class Settings(BaseSettings):
    API_V1_STR = "v1"


settings = Settings()
