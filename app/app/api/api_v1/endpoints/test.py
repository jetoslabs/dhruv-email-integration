import json
import time
from io import BytesIO

from fastapi import APIRouter, Depends
import msal
from loguru import logger
from sqlalchemy.orm import Session

from app.api import deps
from app.apiclients.api_client import ApiClient
from app.apiclients.aws_client import AWSClientHelper, get_tenant_boto3_session
from app.apiclients.endpoint_ms import MsEndpointsHelper
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.core.config import Config, Configuration, configuration
from app.crud.stored_procedures import StoredProcedures
# from app.initial_data import init
from app.schemas.schema_sp import EmailTrackerGetEmailLinkInfoParams

router = APIRouter()


@router.get("/wait")
async def wait_late():
    time.sleep(30)
    return "done"


@router.get("/x")
async def run(tenant: str):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    response, data = await ApiClient('get', config.endpoint, headers=ApiClient.get_headers(token)).retryable_call()
    return data


@router.get("/msgraph/users")
async def run(tenant: str):
    # config = json.load(open('../configuration/ms_auth_configs.json'))
    # config = config["manaliorg"]
    config = configuration.tenant_configurations.get(tenant).azure_auth

    # Create a preferably long-lived app instance which maintains a token cache.
    app = msal.ConfidentialClientApplication(
        config.client_id, authority=config.authority,
        client_credential=config.secret,
        # token_cache=...  # Default cache is in memory only.
                           # You can learn how to use SerializableTokenCache from
                           # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
        )

    # The pattern to acquire a token looks like this.
    result = None

    # Firstly, looks up a token from cache
    # Since we are looking for token for the current app, NOT for an end user,
    # notice we give account parameter as None.
    result = app.acquire_token_silent(config.scope, account=None)

    if not result:
        logger.info("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=config.scope)

    if "access_token" in result:
        # Calling graph using the access token
        # graph_data = requests.get(  # Use token to call downstream service
        #     config['endpoint'],
        #     headers={'Authorization': 'Bearer ' + result['access_token']}, ).json()
        headers = {'Authorization': 'Bearer ' + result['access_token']}
        endpoint = "https://graph.microsoft.com/v1.0/users"
        response, graph_data = await ApiClient('get', endpoint, headers=headers).retryable_call()
        print("Graph API call result: ")
        print(json.dumps(graph_data, indent=2))
        return graph_data
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/load_endpoints_ms")
async def load_endpoints_ms():
    return MsEndpointsHelper._load_endpoints_ms("../configuration/endpoints_ms.json")


# @router.get("/load_global_config")
# async def load_global_config():
#     return GlobalConfigHelper._load_global_config("../configuration/config.yml")


@router.get("/configuration")
async def get_configuration() -> Configuration:
    configuration = Config.validate_and_load("configuration")
    return configuration


@router.get("/save_to_s3")
async def save_to_s3(tenant: str):
    aws_config = configuration.tenant_configurations.get(tenant).aws
    return await AWSClientHelper.save_to_s3(
        get_tenant_boto3_session(tenant),
        BytesIO(b'okokok'),
        aws_config.s3_root_bucket,
        aws_config.s3_default_object_prefix+"okokok.txt")


@router.get("/init_db")
async def init_db():
    logger.info("Creating initial data")
    # init()
    logger.info("Initial data created")
    return "done"


@router.get("/stored_procedure/EmailTrackerGetEmailIDSchema")
async def stored_procedure(db: Session = Depends(deps.get_tenant_sales97_db)):
    res = await StoredProcedures.dhruv_EmailTrackerGetEmailID(db)
    return res


@router.get("/stored_procedure/EmailTrackerGetEmailLinkInfo")
async def stored_procedure(db: Session = Depends(deps.get_tenant_fit_db)):
    res = await StoredProcedures.dhruv_EmailTrackerGetEmailLinkInfo(
        db,
        EmailTrackerGetEmailLinkInfoParams(
            email='fiona.byrd@gmail.com',
            subject='',
            date='02/22/2022'
        )
    )
    return res


class FixedContentQueryChecker:
    def __init__(self, fixed_content: str):
        self.fixed_content = fixed_content

    def __call__(self, q: str = ""):
        if q:
            return self.fixed_content in q
        return False


checker = FixedContentQueryChecker("bar")


class FixedContentQueryChecker1:
    def __init__(self, fixed_content: str):
        self.fixed_content = fixed_content

    def __call__(self, q: str = ""):
        if q:
            return self.fixed_content in q
        return False


checker1 = FixedContentQueryChecker1("foo")


@router.get("/query-checker/")
async def read_query_check(
        is_tenant: bool = Depends(deps.assert_tenant),
        fixed_content_included: bool = Depends(checker),
        fixed_content_included1: bool = Depends(checker1)
):
    return {"fixed_content_in_query": fixed_content_included}