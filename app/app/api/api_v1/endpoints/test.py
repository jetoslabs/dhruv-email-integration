import json
import time
from io import BytesIO
from typing import List, Any

from fastapi import APIRouter, Depends
import msal
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.apiclients.api_client import ApiClient
from app.apiclients.aws_client import AWSClientHelper, boto3_session
from app.apiclients.endpoint_ms import MsEndpointsHelper
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.core.config import GlobalConfigHelper, global_config
from app.crud.stored_procedures import run_stored_procedure, StoredProcedures
from app.initial_data import init
from app.schemas.schema_sp import EmailTrackerGetEmailIDSchema, EmailTrackerGetEmailLinkInfoParams

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


@router.get("/")
async def run():
    config = json.load(open('../configuration/ms_auth_configs.json'))
    config = config["manaliorg"]

    # Create a preferably long-lived app instance which maintains a token cache.
    app = msal.ConfidentialClientApplication(
        config['client_id'], authority=config['authority'],
        client_credential=config['secret'],
        # token_cache=...  # Default cache is in memory only.
                           # You can learn how to use SerializableTokenCache from
                           # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
        )

    # The pattern to acquire a token looks like this.
    result = None

    # Firstly, looks up a token from cache
    # Since we are looking for token for the current app, NOT for an end user,
    # notice we give account parameter as None.
    result = app.acquire_token_silent(config['scope'], account=None)

    if not result:
        logger.info("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=config['scope'])

    if "access_token" in result:
        # Calling graph using the access token
        # graph_data = requests.get(  # Use token to call downstream service
        #     config['endpoint'],
        #     headers={'Authorization': 'Bearer ' + result['access_token']}, ).json()
        headers = {'Authorization': 'Bearer ' + result['access_token']}
        response, graph_data = await ApiClient('get', config['endpoint'], headers=headers).retryable_call()
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


@router.get("/load_global_config")
async def load_global_config():
    return GlobalConfigHelper._load_global_config("../configuration/config.yml")


@router.get("/save_to_s3")
async def save_to_s3():
    return await AWSClientHelper.save_to_s3(
        boto3_session,
        BytesIO(b'okokok'),
        global_config.s3_root_bucket,
        global_config.s3_default_object_prefix+"okokok.txt")


@router.get("/init_db")
async def init_db():
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")
    return "done"


@router.get("/stored_procedure/EmailTrackerGetEmailIDSchema")
async def stored_procedure(db: Session = Depends(deps.get_sales97_db)):
    res = await StoredProcedures.dhruv_EmailTrackerGetEmailID(db)
    return res


@router.get("/stored_procedure/EmailTrackerGetEmailLinkInfo")
async def stored_procedure(db: Session = Depends(deps.get_fit_db)):
    res = await StoredProcedures.dhruv_EmailTrackerGetEmailLinkInfo(
        db,
        EmailTrackerGetEmailLinkInfoParams(
            email='xxxxx@gmail.com',
            date='02/22/2022'
        )
    )
    return res
    # logger.info("Staring stored procedure")
    # # params = {"\@EmailIDInClientAgentSupplier": "fiona.byrd@gmail.com"}
    # # # EmailIDInClientAgentSupplier = "fiona.byrd@gmail.com"
    #
    # res: List[Any] = run_stored_procedure(
    #     db,
    #     "fit.dbo.dhruv_EmailTrackerGetEmailLinkInfo",
    #     ['fiona.byrd@gmail.com', '', '02/22/2022']
    #     # AnyBaseModelSchema=BaseModel
    # )
    # logger.info("Ending stored procedure")
    # return res

