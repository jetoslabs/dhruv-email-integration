import json
import time
from typing import Optional

import requests
from fastapi import APIRouter
import msal
from loguru import logger

from app.api.deps import get_token
from app.apiclients.api_client import ApiClient
from app.apiclients.aws_client import AWSClientHelper
from app.apiclients.endpoint_ms import MsEndpointsHelper
from app.core import config
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token

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
    return await MsEndpointsHelper._load_endpoints_ms("../configuration/endpoints_ms.json")


@router.get("/load_aws_config")
async def load_aws_config():
    return await AWSClientHelper.load_config("../configuration/config.yml")
