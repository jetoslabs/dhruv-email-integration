import time
from typing import List, Tuple

from aiohttp import ClientResponse
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.api import deps
from app.api.api_v1.endpoints.users import get_user_by_email
from app.apiclients.api_client import ApiClient
from app.apiclients.aws_client import AWSClientHelper, boto3_session
from app.apiclients.endpoint_ms import MsEndpointsHelper, endpoints_ms, MsEndpointHelper
from app.controllers.mail import get_attachments_path_from_id, add_filter_to_leave_out_internal_domain_messages, \
    map_MessageResponseSchema_to_SECorrespondenceCreate, map_MessageSchema_to_SECorrespondenceCreate
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.core.config import global_config
from app.crud.crud_correspondence_id import CRUDCorrespondenceId
from app.crud.crud_se_correspondence import CRUDSECorrespondence
from app.crud.stored_procedures import StoredProcedures
from app.models import CorrespondenceId
from app.models.se_correspondence import SECorrespondence
from app.schemas.schema_db import CorrespondenceIdCreate, CorrespondenceCreate, SECorrespondenceCreate
from app.schemas.schema_ms_graph import MessagesSchema, MessageResponseSchema, AttachmentsSchema, \
    SendMessageRequestSchema, CreateMessageSchema, MessageBodySchema, EmailAddressWrapperSchema, EmailAddressSchema, \
    AttachmentInCreateMessage, AttachmentSchema
from app.schemas.schema_sp import EmailTrackerGetEmailIDSchema, EmailTrackerGetEmailLinkInfo, EmailTrackerGetEmailLinkInfoParams

router = APIRouter()


@router.get("/users/{id}/messages", response_model=MessagesSchema)
async def get_messages(tenant: str, id: str, top: int = 5, filter: str = "") -> MessagesSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        endpoint = MsEndpointsHelper.get_endpoint("message:list", endpoints_ms)
        endpoint.request_params['id'] = id
        endpoint.optional_query_params.top = str(top) if 0 < top <= 1000 else str(10)
        # TODO: uncomment the line below
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


@router.get("/users/{id}/messages/{message_id}/save")
async def save_message(tenant: str, id: str, message_id: str, db: Session = Depends(deps.get_mailstore_db)):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        message: MessageResponseSchema = await get_message(tenant, id, message_id)
        # get email link info from dhruv
        emailTrackerGetEmailLinkInfoParams = EmailTrackerGetEmailLinkInfoParams(
            email=message.from_email.emailAddress.address,
            date=message.sentDateTime  #
        )
        email_links_info = await StoredProcedures.dhruv_EmailTrackerGetEmailLinkInfo(
            db,
            emailTrackerGetEmailLinkInfoParams
        )
        email_link_info: EmailTrackerGetEmailLinkInfo = email_links_info[0]
        if email_link_info.AccountCode == '':
            logger.bind(
                emailTrackerGetEmailLinkInfoParams=emailTrackerGetEmailLinkInfoParams
            ).error("No link found in Dhruv, EmailTrackerGetEmailLinkInfo result is empty")
            return

        # save message to SECorrespondence table
        loop_start_epoch: str = str(int(time.time()))
        obj_in = map_MessageResponseSchema_to_SECorrespondenceCreate(
            message, email_link_info, loop_start_epoch
        )

        new_row = CRUDSECorrespondence(SECorrespondence).create(db, obj_in=obj_in)
        return new_row
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/users/{id}/messages1/save")
async def save_user_messages(tenant: str, id: str, top: int = 5, filter="", db: Session = Depends(deps.get_mailstore_db)):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        messages_schema: MessagesSchema = await get_messages(tenant, id, top=top, filter=filter)
        messages = messages_schema.value

        if messages is None:
            raise HTTPException(status_code=204, detail="No messages found")

        loop_start_epoch: str = str(int(time.time()))
        se_correspondence_create_schemas = []
        for message in messages:
            try:
                email_to_check = message.from_email.emailAddress.address
                date_to_check = message.sentDateTime
                email_link_info = await get_email_link_from_dhruv(email_to_check, date_to_check, db)
                if email_link_info.AccountCode == '':
                    logger.bind(email=email_to_check, date=date_to_check, email_link_info=email_link_info).error("Not found in Dhruv: email_link_info")
                obj_in = map_MessageSchema_to_SECorrespondenceCreate(
                    message, email_link_info, loop_start_epoch
                )
                se_correspondence_create_schemas.append(obj_in)
            except Exception as e:
                logger.bind(message=message).error(e)
        se_correspondence_rows = CRUDSECorrespondence(
            SECorrespondence
        ).get_by_mail_unique_id_or_create_get_if_not_exist_multi(
            db,
            obj_ins=se_correspondence_create_schemas
        )

        return [f"{r.SeqNo} - {r.MailFrom} - {r.MailSubject}" for r in se_correspondence_rows]
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))  # You may need this when reporting a bug


async def get_email_link_from_dhruv(email: str, date: str, db: Session) ->  EmailTrackerGetEmailLinkInfo:
    # get email link info from dhruv
    emailTrackerGetEmailLinkInfoParams = EmailTrackerGetEmailLinkInfoParams(
        email=email, #message.from_email.emailAddress.address,
        date=date #message.sentDateTime  #
    )
    email_links_info = await StoredProcedures.dhruv_EmailTrackerGetEmailLinkInfo(
        db,
        emailTrackerGetEmailLinkInfoParams
    )
    return email_links_info[0]

@router.get("/messages1/save")
async def save_tenant_messages(
        tenant: str,
        top: int = 5,
        filter="",
        db_sales97: Session = Depends(deps.get_sales97_db),
        db_fit: Session = Depends(deps.get_fit_db)
):
    # get list of trackable users
    users_to_track: List[EmailTrackerGetEmailIDSchema] = await StoredProcedures.dhruv_EmailTrackerGetEmailID(db_sales97)
    # get user ids for those email ids
    users = []
    for user_to_track in users_to_track:
        user = await get_user_by_email(tenant, user_to_track.EMailId)
        if user is None:
            logger.bind(user_to_track=user_to_track).error("Cannot find in Azure")
        else:
            logger.bind(user_to_track=user_to_track).debug("Found in Azure")
            users.append(user)
    # call save_user_messages for each user id
    all_saves = []
    for user in users:
        saves = await save_user_messages(tenant, user.id)
        all_saves.append(saves)
        logger.bind(user=user, saves=saves).info("Saved user messages")
    return all_saves


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
