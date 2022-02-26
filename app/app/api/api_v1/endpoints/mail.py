import base64
from io import BytesIO
from typing import List, Tuple, Optional, Union

from aiohttp import ClientResponse
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.api import deps
from app.apiclients.api_client import ApiClient
from app.apiclients.aws_client import AWSClientHelper, boto3_session
from app.apiclients.endpoint_ms import MsEndpointsHelper, endpoints_ms, MsEndpointHelper
from app.controllers.mail import get_attachments_path_from_id, add_filter_to_leave_out_internal_domain_messages
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.core.config import global_config
from app.crud.crud_correspondence import CRUDCorrespondence
from app.crud.crud_correspondence_id import CRUDCorrespondenceId
from app.models import CorrespondenceId, Correspondence
from app.schemas.schema_db import CorrespondenceIdCreate, CorrespondenceCreate
from app.schemas.schema_ms_graph import MessagesSchema, MessageResponseSchema, AttachmentsSchema, \
    SendMessageRequestSchema, CreateMessageSchema, MessageBodySchema, EmailAddressWrapperSchema, EmailAddressSchema, \
    AttachmentInCreateMessage, AttachmentSchema

router = APIRouter()


@router.get("/users/{id}/messages", response_model=MessagesSchema)
async def get_messages(tenant: str, id: str, top: int = 5, filter: str = "") -> MessagesSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        endpoint = MsEndpointsHelper.get_endpoint("message:list", endpoints_ms)
        endpoint.request_params['id'] = id
        endpoint.optional_query_params.top = str(top) if 0 < top <= 1000 else str(10)
        new_filter = add_filter_to_leave_out_internal_domain_messages(tenant, filter)
        if new_filter != "":
            endpoint.optional_query_params.filter = new_filter
        url = MsEndpointHelper.form_url(endpoint)
        # url = f"{url}?$filter=receivedDateTime gt 2022-02-07T02:56:37Z"

        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=30)
        response, data = await api_client.retryable_call()
        return MessagesSchema(**data) if type(data) == dict else data
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/users/{id}/messages/{message_id}", response_model=MessageResponseSchema)
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


@router.get("/users/{id}/messages/{message_id}/attachments", response_model=AttachmentsSchema)
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


@router.get("/users/{id}/messages/{message_id}/attachments/save", response_model=List[str])
async def save_message_attachments(
        tenant: str, id: str, message_id: str, db: Session = Depends(deps.get_db)
) -> List[str]:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        links = []
        data: Union[dict, AttachmentsSchema] = await list_message_attachments(tenant, id, message_id)
        if type(data) == dict: data = AttachmentsSchema(**data)
        attachments: List[AttachmentSchema] = data.value
        for attachment in attachments:
            if attachment.contentBytes is not None:
                logger.bind(filename=attachment.name, content_length=len(attachment.contentBytes)).debug("attachment")
                filename = attachment.name
                content_b64 = attachment.contentBytes
                # contentBytes is base64 encoded str
                content = base64.b64decode(content_b64)
                # s3_path = get_s3_path_from_ms_message_id(db, message_id)
                id_record = CRUDCorrespondenceId(CorrespondenceId).get_by_message_id_or_create_if_not_exist(
                    db, obj_in=CorrespondenceIdCreate(message_id=message_id))
                # if id_record is None:
                #     raise HTTPException(status_code=500)
                s3_path = get_attachments_path_from_id(id_record.id)
                saved_s3_path = await AWSClientHelper.get_or_save_get_in_s3(
                    boto3_session, BytesIO(content), global_config.s3_root_bucket, f"{s3_path}/{filename}"
                )
                links.append(saved_s3_path)
            else:
                logger.bind(attachment=attachment).info("No content")
        if len(links) == 0:
            # raise HTTPException(status_code=204, detail="Nothing saved") # TODO: bring back in some form
            pass
        return links
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/users/{id}/messages/{message_id}/save")
async def save_message(tenant: str, id: str, message_id: str, db: Session = Depends(deps.get_db)):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        message: MessageResponseSchema = await get_message(tenant, id, message_id)
        # save message to correspondenceId table
        correspondence_id_record = CRUDCorrespondenceId(CorrespondenceId).get_by_message_id_or_create_if_not_exist(
            db, obj_in=CorrespondenceIdCreate(message_id=message_id)
        )
        if correspondence_id_record is None:
            raise HTTPException(status_code=400)
        # save message to Correspondence table
        new_row = CRUDCorrespondence(Correspondence).get_by_message_id_or_create_get_if_not_exist(
            db, obj_in=CorrespondenceCreate(
                message_id=message_id,
                subject=message.subject,
                body=message.body.content,
                attachments=",".join(await save_message_attachments(tenant, id, message_id, db)),
                from_address=message.from_email.emailAddress.address,
                to_address=",".join([r.emailAddress.address for r in message.toRecipients])
            )
        )
        # if new_row is None:
        #     raise HTTPException(status_code=204, detail="Nothing saved, Already Exist")
        return new_row
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/users/{id}/save/messages")
async def save_all_messages(tenant: str, id: str, top: int = 5, filter="", db: Session = Depends(deps.get_db)):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        messages_schema: MessagesSchema = await get_messages(tenant, id, top=top, filter=filter)
        messages = messages_schema.value

        if messages is None:
            raise HTTPException(status_code=204, detail="No messages found")

        correspondence_id_create_schemas = []
        for message in messages:
            correspondence_id_create_schemas.append(CorrespondenceIdCreate(message_id=message.id))
        correspondence_id_rows = CRUDCorrespondenceId(CorrespondenceId)\
            .get_by_message_id_or_create_if_not_exist_multi(db, obj_ins=correspondence_id_create_schemas)

        correspondence_create_schemas = []
        for message in messages:
            attachments = await save_message_attachments(tenant, id, message.id, db)
            try:
                correspondence_create_attachments = ",".join(attachments) if attachments is not None else None
            except Exception as e:
                raise e
            correspondence_create = CorrespondenceCreate(
                message_id=message.id,
                subject=message.subject,
                body=message.body.content,
                attachments=correspondence_create_attachments,
                from_address=message.from_email.emailAddress.address,
                to_address=",".join([r.emailAddress.address for r in message.toRecipients])
            )
            correspondence_create_schemas.append(correspondence_create)
        correspondence_rows = CRUDCorrespondence(Correspondence).get_by_message_id_or_create_get_if_not_exist_multi(db, obj_ins=correspondence_create_schemas)
        return [f"{r.id} - {r.subject}" for r in correspondence_rows]
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.post("/users/{id}/sendMail", status_code=202)
async def send_mail(tenant: str, id: str):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        message_to_send = SendMessageRequestSchema(
            message=CreateMessageSchema(
                subject="program mail send 2",
                body=MessageBodySchema(
                    contentType="HTML",
                    content="okokok___okokok 2"
                ),
                toRecipients=[EmailAddressWrapperSchema(
                    emailAddress=EmailAddressSchema(
                        name="Adele Vance",
                        address="AdeleV@26cfkx.onmicrosoft.com"
                    )
                )],
                ccRecipients=[EmailAddressWrapperSchema(
                    emailAddress=EmailAddressSchema(
                        name="Adele Vance",
                        address="AdeleV@26cfkx.onmicrosoft.com"
                    )
                )],
                attachments=[
                    AttachmentInCreateMessage(
                        odata_type="#microsoft.graph.fileAttachment",
                        name="attachment.txt",
                        contentType="text/plain",
                        contentBytes="SGVsbG8gV29ybGQh"
                    )
                ]
            )
        )

        endpoint = MsEndpointsHelper.get_endpoint("message:send", endpoints_ms)
        endpoint.request_params["id"] = id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(
            endpoint.request_method,
            url,
            headers=ApiClient.get_headers(token),
            data=message_to_send.json(),
            timeout_sec=3000)
        api_client.headers['content-type'] = "application/json"
        response_and_data: Tuple[ClientResponse, str] = await api_client.retryable_call()
        response, data = response_and_data
        return JSONResponse(status_code=response.status, content={"message": data})
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug
