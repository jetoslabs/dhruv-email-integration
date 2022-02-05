import json

from fastapi import APIRouter

from app.apiclients.api_client import ApiClient
from app.apiclients.endpoint_ms import MsEndpointsHelper, endpoints_ms, MsEndpointHelper
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token

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