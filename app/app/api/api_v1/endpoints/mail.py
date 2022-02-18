import base64
from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.apiclients.api_client import ApiClient
from app.apiclients.aws_client import AWSClientHelper, boto3_session
from app.apiclients.endpoint_ms import MsEndpointsHelper, endpoints_ms, MsEndpointHelper
from app.controllers.mail import get_s3_path_from_ms_message_id
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.core.config import global_config
from app.crud.crud_correspondence import CRUDCorrespondence
from app.crud.crud_correspondence_id import CRUDCorrespondenceId
from app.models import CorrespondenceId, Correspondence
from app.schemas.schema_db import CorrespondenceIdCreate, CorrespondenceCreate
from app.schemas.schema_ms_graph import MessagesSchema, MessageResponseSchema, AttachmentsSchema

router = APIRouter()


@router.get("/{id}/messages", response_model=MessagesSchema)
async def get_messages(tenant: str, id: str, top: int = 5, filter: str = "") -> MessagesSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        endpoint = MsEndpointsHelper.get_endpoint("message:list", endpoints_ms)
        endpoint.request_params['id'] = id
        endpoint.optional_query_params.top = str(top) if 0 < top <= 1000 else str(10)
        if filter != "": endpoint.optional_query_params.filter = filter
        url = MsEndpointHelper.form_url(endpoint)
        # url = f"{url}?$filter=receivedDateTime gt 2022-02-07T02:56:37Z"

        api_client = ApiClient(
            endpoint.request_method,
            url,
            headers=ApiClient.get_headers(token),
            timeout_sec=30
        )
        response, data = await api_client.retryable_call()
        return MessagesSchema(**data) if type(data) == dict else data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/{id}/messages/{message_id}", response_model=MessageResponseSchema)
async def get_message(tenant: str, id: str, message_id: str) -> MessageResponseSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        endpoint = MsEndpointsHelper.get_endpoint("message:get", endpoints_ms)
        endpoint.request_params["id"] = id
        endpoint.request_params["message_id"] = message_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=3000)
        response, data = await api_client.retryable_call()
        return MessageResponseSchema(**data) if type(data) == dict else data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


# @router.get("/{id}/messages/{message_id}/$value")
# async def get_message_mime(tenant: str, id: str, message_id: str):
#     config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
#     if "access_token" in token:
#         endpoint = MsEndpointsHelper.get_endpoint("message:get:mime", endpoints_ms)
#         endpoint.request_params["id"] = id
#         endpoint.request_params["message_id"] = message_id
#         url = MsEndpointHelper.form_url(endpoint)
#         api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=3000)
#         response, data = await api_client.retryable_call()
#         return data
#     else:
#         print(token.get("error"))
#         print(token.get("error_description"))
#         print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/{id}/messages/{message_id}/attachments", response_model=AttachmentsSchema)
async def list_message_attachments(tenant: str, id: str, message_id: str) -> AttachmentsSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        endpoint = MsEndpointsHelper.get_endpoint("message:list:attachment", endpoints_ms)
        endpoint.request_params["id"] = id
        endpoint.request_params["message_id"] = message_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=3000)
        response, data = await api_client.retryable_call()
        return AttachmentsSchema(**data) if type(data) == 'dict' else data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/{id}/messages/{message_id}/attachments/save", response_model=List[str])
async def save_message_attachments(
        tenant: str, id: str, message_id: str, db: Session = Depends(deps.get_db)
) -> List[str]:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        links = []
        data = await list_message_attachments(tenant, id, message_id)
        attachments: list = data["value"]
        for attachment in attachments:
            filename = attachment["name"]
            content_b64 = attachment["contentBytes"]
            # contentBytes is base64 encoded str
            content = base64.b64decode(content_b64)
            s3_path = get_s3_path_from_ms_message_id(db, message_id)
            saved_s3_path = await AWSClientHelper.save_to_s3(
                boto3_session, BytesIO(content), global_config.s3_root_bucket, f"{s3_path}/{filename}"
            )
            links.append(saved_s3_path)
        return links

    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/{id}/messages/{message_id}/save")
async def save_message(tenant: str, id: str, message_id: str, db: Session = Depends(deps.get_db)):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        message: MessageResponseSchema = await get_message(tenant, id, message_id)
        # save message to correspondenceId table
        correspondence_id_record = CRUDCorrespondenceId(CorrespondenceId).create(
            db, obj_in=CorrespondenceIdCreate(message_id=message_id)
        )
        # save message to Correspondence table
        new_row = CRUDCorrespondence(Correspondence).create(
            db, obj_in=CorrespondenceCreate(
                message_id=message_id,
                subject=message.subject,
                body=message.body.content,
                attachments=",".join(await save_message_attachments(tenant, id, message_id, db)),
                from_address=message.from_email.emailAddress.address,
                to_address=",".join([r.emailAddress.address for r in message.toRecipients])
            )
        )
        return new_row
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/{id}/save/messages")
async def save_all_messages(tenant: str, id: str, db: Session = Depends(deps.get_db)):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        messages_schema: MessagesSchema = await get_messages(tenant, id)
        messages = messages_schema.value

        correspondence_id_create_schemas = []
        for message in messages:
            correspondence_id_create_schemas.append(CorrespondenceIdCreate(message_id=message.id))
        correspondence_id_rows = CRUDCorrespondenceId(CorrespondenceId).create_multi(db, obj_ins=correspondence_id_create_schemas)

        correspondence_create_schemas = []
        for message in messages:
            correspondence_create_schemas.append(
                CorrespondenceCreate(
                    message_id=message.id,
                    subject=message.subject,
                    body=message.body.content,
                    attachments=",".join(await save_message_attachments(tenant, id, message.id, db)),
                    from_address=message.from_email.emailAddress.address,
                    to_address=",".join([r.emailAddress.address for r in message.toRecipients])
                )
            )
        correspondence_rows = CRUDCorrespondence(Correspondence).create_multi(db, obj_ins=correspondence_create_schemas)
        return correspondence_rows
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