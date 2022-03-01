import time
from typing import List, Tuple, Optional

from aiohttp import ClientResponse
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.api import deps
from app.api.api_v1.endpoints.users import get_user_by_email, get_user
from app.apiclients.api_client import ApiClient
from app.apiclients.endpoint_ms import MsEndpointsHelper, endpoints_ms, MsEndpointHelper
from app.controllers.mail import MailController
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.crud.stored_procedures import StoredProcedures
from app.models.se_correspondence import SECorrespondence
from app.schemas.schema_ms_graph import MessagesSchema, MessageResponseSchema, AttachmentsSchema, \
    SendMessageRequestSchema, CreateMessageSchema, MessageBodySchema, EmailAddressWrapperSchema, EmailAddressSchema, \
    AttachmentInCreateMessage, UserResponseSchema, MessageSchema, UserSchema
from app.schemas.schema_sp import EmailTrackerGetEmailIDSchema, EmailTrackerGetEmailLinkInfo, \
    EmailTrackerGetEmailLinkInfoParams

router = APIRouter()


@router.get("/users/{id}/messages", response_model=MessagesSchema)
async def get_messages(tenant: str, id: str, top: int = 5, filter: str = "") -> MessagesSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        messages: Optional[MessagesSchema] = await MailController.get_messages(token, tenant, id, top, filter)
        if messages is None:
            raise HTTPException(status_code=404)
        return messages
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.get("/users/{id}/messages/{message_id}", response_model=MessageResponseSchema)
async def get_message(tenant: str, id: str, message_id: str) -> MessageResponseSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        message: Optional[MessageResponseSchema] = await MailController.get_message(token, id, message_id)
        if message is None:
            raise HTTPException(status_code=404)
        return message
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.get("/users/{id}/messages/{message_id}/attachments", response_model=AttachmentsSchema)
async def list_message_attachments(tenant: str, id: str, message_id: str) -> AttachmentsSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        attachments: Optional[AttachmentsSchema] = await MailController.get_message_attachments(token, id, message_id)
        return attachments
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.get("/users/{id}/messages/{message_id}/attachments/save", response_model=List[str])
async def save_message_attachments(
        tenant: str, id: str, message_id: str, db: Session = Depends(deps.get_mailstore_db)
) -> List[str]:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        attachments_schema: AttachmentsSchema = await MailController.get_message_attachments(token, id, message_id)
        attachments = attachments_schema.value
        if attachments is None:
            raise HTTPException(status_code=404)
        links: Optional[List[str]] = await MailController.save_message_attachments(db, message_id, attachments)
        if links is None:
            raise HTTPException(status_code=500)  # links is None when mail is not found in db
        return links
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)
    #     links = []
    #     data: Union[dict, AttachmentsSchema] = await list_message_attachments(tenant, id, message_id)
    #     if type(data) == dict: data = AttachmentsSchema(**data)
    #     attachments: List[AttachmentSchema] = data.value
    #     for attachment in attachments:
    #         if attachment.contentBytes is not None:
    #             logger.bind(filename=attachment.name, content_length=len(attachment.contentBytes)).debug("attachment")
    #             filename = attachment.name
    #             content_b64 = attachment.contentBytes
    #             # contentBytes is base64 encoded str
    #             content = base64.b64decode(content_b64)
    #             id_record = CRUDSECorrespondence(SECorrespondence).get_by_mail_unique_id(db, mail_unique_id=message_id)
    #             if id_record is None:
    #                 # raise HTTPException(status_code=500)
    #                 logger.bind().error("Cannot find mail_id")
    #             file_relative_path = get_attachments_path_from_id(id_record.SeqNo)
    #             saved_to = await FileHelper.get_or_save_get_in_disk(
    #                 BytesIO(content), global_config.disk_base_path, file_relative_path, filename
    #             )
    #             logger.bind(saved_to=saved_to).info("Saved to disk")
    #             links.append(saved_to)
    #         else:
    #             logger.bind(attachment=attachment).info("No content")
    #     if len(links) == 0:
    #         # raise HTTPException(status_code=204, detail="Nothing saved") # TODO: bring back in some form
    #         pass
    #     return links
    # else:
    #     print(token.get("error"))
    #     print(token.get("error_description"))
    #     print(token.get("correlation_id"))  # You may need this when reporting a bug


@router.get("/users/{id}/messages/{message_id}/save")
async def save_message(
        tenant: str,
        id: str,
        message_id: str,
        db_fit: Session = Depends(deps.get_fit_db),
        db_mailstore: Session = Depends(deps.get_mailstore_db),
):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        # message: MessageResponseSchema = await get_message(tenant, id, message_id)
        req_epoch: str = str(int(time.time()))
        # get messages
        message_response_schema: Optional[MessageResponseSchema] = await MailController.get_message(token, id, message_id)
        if message_response_schema is None:
            raise HTTPException(status_code=204, detail="No messages found")
        message = MessageSchema(**(message_response_schema.dict()))
        # get user
        user_dict:  Optional[UserResponseSchema] = await get_user(tenant, id)  # TODO: Write UserController.get_user
        if user_dict is None:
            raise HTTPException(status_code=500)
        user: UserResponseSchema = UserResponseSchema(**user_dict)
        # save messages
        se_correspondence_rows: List[SECorrespondence] = \
            await MailController.save_user_messages(tenant, user, [message], db_fit, db_mailstore, req_epoch)
        # save attachments
        links = []
        for se_correspondence_row in se_correspondence_rows:
            message_links = await save_message_attachments(tenant, id, se_correspondence_row.MailUniqueId, db_mailstore)
            links.append(",".join(message_links))
        return se_correspondence_rows, links
        # # get email link info from dhruv
        # emailTrackerGetEmailLinkInfoParams = EmailTrackerGetEmailLinkInfoParams(
        #     email=message.from_email.emailAddress.address,
        #     date=message.sentDateTime  #
        # )
        # email_links_info = await StoredProcedures.dhruv_EmailTrackerGetEmailLinkInfo(
        #     db,
        #     emailTrackerGetEmailLinkInfoParams
        # )
        # email_link_info: EmailTrackerGetEmailLinkInfo = email_links_info[0]
        # if email_link_info.AccountCode == '':
        #     logger.bind(
        #         emailTrackerGetEmailLinkInfoParams=emailTrackerGetEmailLinkInfoParams
        #     ).error("No link found in Dhruv, EmailTrackerGetEmailLinkInfo result is empty")
        #     return
        #
        # # save message to SECorrespondence table
        # loop_start_epoch: str = str(int(time.time()))
        # obj_in = map_MessageResponseSchema_to_SECorrespondenceCreate(
        #     message, email_link_info, loop_start_epoch
        # )
        #
        # new_row = CRUDSECorrespondence(SECorrespondence).create(db, obj_in=obj_in)
        # links = await save_message_attachments(tenant, id, message_id)
        # return new_row
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.get("/users/{id}/messages1/save")
async def save_user_messages(
        tenant: str,
        id: str,
        top: int = 5,
        filter="",
        db_fit: Session = Depends(deps.get_fit_db),
        db_mailstore: Session = Depends(deps.get_mailstore_db)
) -> (List[SECorrespondence], List[str]):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        req_epoch: str = str(int(time.time()))
        # get messages
        messages_schema: Optional[MessagesSchema] = await MailController.get_messages(token, tenant, id, top, filter)
        messages: Optional[List[MessageSchema]] = None
        try:
            messages = messages_schema.value
        except Exception as e:
            print(e)
        if messages is None or len(messages) == 0:
            raise HTTPException(status_code=204, detail="No messages found")
        # get user
        user_dict:  Optional[UserResponseSchema] = await get_user(tenant, id)  # TODO: Write UserController.get_user
        if user_dict is None:
            raise HTTPException(status_code=500)
        user: UserResponseSchema = UserResponseSchema(**user_dict)
        # save messages
        se_correspondence_rows: List[SECorrespondence] = \
            await MailController.save_user_messages(tenant, user, messages, db_fit, db_mailstore, req_epoch)
        # save attachments
        links = []
        for se_correspondence_row in se_correspondence_rows:
            if se_correspondence_row.HasAttachment:
                message_links = await save_message_attachments(tenant, id, se_correspondence_row.MailUniqueId, db_mailstore)
                links.append(",".join(message_links))
        return se_correspondence_rows, links
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


async def get_email_link_from_dhruv(email: str, date: str, db: Session) ->  EmailTrackerGetEmailLinkInfo:
    # get email link info from dhruv
    emailTrackerGetEmailLinkInfoParams = EmailTrackerGetEmailLinkInfoParams(email=email, date=date)
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
        db_fit: Session = Depends(deps.get_fit_db),
        db_mailstore: Session = Depends(deps.get_mailstore_db)
) -> (List[UserSchema], List[SECorrespondence], List[str]):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        # get list of trackable users
        users_to_track: List[EmailTrackerGetEmailIDSchema] = await StoredProcedures.dhruv_EmailTrackerGetEmailID(db_sales97)
        # get user ids for those email ids
        users: List[UserSchema] = []
        for user_to_track in users_to_track:
            user = await get_user_by_email(tenant, user_to_track.EMailId)
            if user is None:
                logger.bind(user_to_track=user_to_track).error("Cannot find in Azure")
            else:
                logger.bind(user_to_track=user_to_track).debug("Found in Azure")
                users.append(user)
        # call save_user_messages for each user id
        all_rows = []
        all_links = []
        for user in users:
            try:
                rows, links = await save_user_messages(tenant, user.id, top, filter, db_fit, db_mailstore)
                logger.bind(tenant=tenant, user=user, rows=len(rows), links=len(links)).info("Saved user messages")
                if len(rows) > 0: all_rows.append(rows)
                if len(links) > 0: all_links.append(",".join(links))
            except Exception as e:
                logger.bind(
                    error=token.get("error"),
                    error_description=token.get("error_description"),
                    correlation_id=token.get("correlation_id")
                ).error(f"investigate:\n {e}")
                continue
        return users, all_rows, all_links


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
