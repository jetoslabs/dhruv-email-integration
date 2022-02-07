import base64
from io import BytesIO

from fastapi import APIRouter

from app.apiclients.api_client import ApiClient
from app.apiclients.aws_client import AWSClientHelper, boto3_session
from app.apiclients.endpoint_ms import MsEndpointsHelper, endpoints_ms, MsEndpointHelper
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.core.config import global_config

router = APIRouter()


@router.get("/{id}/messages")
async def list_mail(tenant: str, id: str):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        endpoint = MsEndpointsHelper.get_endpoint("message:list", endpoints_ms)
        endpoint.request_params['id'] = id
        url = MsEndpointHelper.form_url(endpoint)

        api_client = ApiClient(
            endpoint.request_method,
            url,
            headers=ApiClient.get_headers(token),
            timeout_sec=30
        )
        response, data = await api_client.retryable_call()
        return data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/{id}/messages/{message_id}")
async def get_message(tenant: str, id: str, message_id: str):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        endpoint = MsEndpointsHelper.get_endpoint("message:get", endpoints_ms)
        endpoint.request_params["id"] = id
        endpoint.request_params["message_id"] = message_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=3000)
        response, data = await api_client.retryable_call()
        return data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/{id}/messages/{message_id}/$value")
async def get_message_mime(tenant: str, id: str, message_id: str):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        endpoint = MsEndpointsHelper.get_endpoint("message:get:mime", endpoints_ms)
        endpoint.request_params["id"] = id
        endpoint.request_params["message_id"] = message_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=3000)
        response, data = await api_client.retryable_call()
        return data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/{id}/messages/{message_id}/attachments")
async def list_message_attachments(tenant: str, id: str, message_id: str):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        endpoint = MsEndpointsHelper.get_endpoint("message:list:attachment", endpoints_ms)
        endpoint.request_params["id"] = id
        endpoint.request_params["message_id"] = message_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=3000)
        response, data = await api_client.retryable_call()
        return data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/{id}/messages/{message_id}/attachments/save")
async def save_message_attachment(tenant: str, id: str, message_id: str):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        data = await list_message_attachments(tenant, id, message_id)
        attachments: list = data["value"]
        for attachment in attachments:
            filename = attachment["name"]
            content_b64 = attachment["contentBytes"]
            # contentBytes is base64 encoded str
            content = base64.b64decode(content_b64)
            is_saved = await AWSClientHelper.save_to_s3(boto3_session, BytesIO(content), global_config.s3_root_bucket, filename)

    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug




# @router.post("/sendMail")
# async def send_mail(tenant="manaliorg"):
#     data = {
#       "message": {
#         "subject": "Meet for lunch?",
#         "body": {
#           "contentType": "Text",
#           "content": "The new cafeteria is open."
#         },
#         "toRecipients": [
#           {
#             "emailAddress": {
#               "address": "toanuragjha@gmail.com"
#             }
#           }
#         ],
#         "ccRecipients": [
#           {
#             "emailAddress": {
#               "address": "mmpatil34@gmail.com"
#             }
#           }
#         ]
#       },
#     }
#     data = json.dumps(data)
#     config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
#     if "access_token" in token:
#         response, data = await ApiClient(
#             'post',
#             str(Endpoint.send_mail.value).replace("{id}", "4557db1f-edc7-4c95-8874-0b5ca2fbb42e"),
#             headers=ApiClient.get_headers(token),
#             data=data,
#             timeout_sec=3000
#         ).retryable_call()
#         return data
#     else:
#         print(token.get("error"))
#         print(token.get("error_description"))
#         print(token.get("correlation_id"))  # You may need this when reporting a bug