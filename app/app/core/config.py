import json

import yaml
from loguru import logger
from pydantic import BaseModel


class GlobalConfig(BaseModel):
    tenant: str
    aws_access_key_id: str
    aws_access_secret: str
    aws_region: str
    aws_output: str
    s3_root_bucket: str
    s3_default_bucket: str


class GlobalConfigHelper:
    @staticmethod
    def _load_global_config() -> GlobalConfig:
        try:
            with open("../configuration/global_config.yml") as file:
                global_config_dict = yaml.safe_load(file)
                config = GlobalConfig(**global_config_dict)
                return config
        except Exception as e:
            logger.bind().error("Error while loading global_config... exiting...")
            raise e


global_config = GlobalConfigHelper._load_global_config()
