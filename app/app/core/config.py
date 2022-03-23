import os
from enum import Enum
from typing import Dict, List, Optional

import yaml
from loguru import logger
from pydantic import BaseModel

from app.core.settings import settings


class GlobalConfig(BaseModel):
    tenant: str

    db_url: str
    db_pwd: str
    db_sales97_name: str
    db_fit_name: str
    db_mailstore_name: str

    aws_access_key_id: str
    aws_access_secret: str
    aws_region: str
    aws_output: str
    s3_root_bucket: str
    s3_default_object_prefix: str
    disk_base_path: str


class GlobalConfigHelper:
    @staticmethod
    def _load_global_config(filepath: str) -> GlobalConfig:
        try:
            with open(filepath) as file:
                global_config_dict = yaml.safe_load(file)
                config = GlobalConfig(**global_config_dict)
                return config
        except Exception as e:
            logger.bind().error(f"cwd={os.getcwd()}")
            logger.bind().error("Error while loading global_config... exiting")
            raise e


# TODO: move var
# global_config = GlobalConfigHelper._load_global_config("../configuration/global_config.yml")
global_config = GlobalConfigHelper._load_global_config(
    f"{settings.CONFIGURATION_PATH}configuration/global_config.yml"
)


class Tenant(BaseModel):
    tenant: str


class SystemConfiguration(Tenant):
    pass


class AzureAuth(BaseModel):
    authority: str
    client_id: str
    scope: List[str]
    secret: str
    internal_domains: List[str]


class DB(BaseModel):
    db_url: str
    db_pwd: str
    db_sales97_name: str
    db_fit_name: str
    db_mailstore_name: str


class AWS(BaseModel):
    aws_access_key_id: str
    aws_access_secret: str
    aws_region: str
    aws_output: str
    s3_root_bucket: str
    s3_default_object_prefix: str


class Disk(BaseModel):
    disk_base_path: str


class JobType(Enum):
    EmailIntegrate = 'EmailIntegrate'


class Job(BaseModel):
    name: str
    job_type: JobType


class MailIntegrateJobDependency(Enum):
    DhruvOrigin = 'DhruvOrigin'
    EmailLink = 'EmailLink'


class MailIntegrateJob(Job):
    job_type: JobType = JobType.EmailIntegrate
    dependencies: List[MailIntegrateJobDependency]


class TenantConfiguration(Tenant):
    azure_auth: AzureAuth
    db: DB
    aws: Optional[AWS]
    disk: Disk
    mail_integrate_job: Optional[MailIntegrateJob]


class Configuration(BaseModel):
    system_configuration: SystemConfiguration
    tenant_configurations: Dict[str, TenantConfiguration]

    def get_ms_auth_config(self, tenant: str) -> AzureAuth:
        return self.tenant_configurations.get(tenant).azure_auth


class ConfigurationException(Exception):
    pass


class Config:

    @staticmethod
    def validate_and_load(configuration_path: str) -> Configuration:
        # check if configuration_path is a dir
        if not os.path.isdir(configuration_path):
            raise ConfigurationException()
        # check if "SYSTEM" config exists
        if not os.path.exists(f"{configuration_path}/config.yml"):
            raise ConfigurationException()
        # System Configuration
        system_configuration_dict = Config._load_yaml(f"{configuration_path}/config.yml")
        system_configuration = SystemConfiguration(**system_configuration_dict)
        # list all tenant dir within configuration dir
        tenant_config_dirs = []
        for dir, sub_dirs, _ in os.walk(configuration_path):
            if dir == configuration_path:
                tenant_config_dirs = sub_dirs
                break
        # Tenants Configuration
        tenant_configurations: Dict[str, TenantConfiguration] = {}
        for tenant_config_dir in tenant_config_dirs:
            for dir, sub_dirs, files in os.walk(f"{configuration_path}/{tenant_config_dir}"):
                if "config.yml" in files:
                    tenant_configuration_dict = Config._load_yaml(f"{dir}/config.yml")
                    tenant_configuration = TenantConfiguration(**tenant_configuration_dict)
                    tenant_configurations[tenant_configuration.tenant] = tenant_configuration
        config = Configuration(
            system_configuration=system_configuration,
            tenant_configurations=tenant_configurations
        )
        return config

    @staticmethod
    def _load_yaml(filepath: str) -> dict:
        try:
            with open(filepath) as file:
                data = yaml.safe_load(file)
                return data
        except Exception as e:
            logger.bind().error(f"cwd={os.getcwd()}")
            logger.bind().error("Error while loading yml file")
            raise e


configuration = Config.validate_and_load("../configuration")
