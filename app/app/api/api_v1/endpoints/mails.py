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
from app.controllers.mail import MailController, \
    map_inplace_SendMessageRequestSchema_to_msgrapgh_SendMessageRequestSchema
from app.controllers.user import UserController
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.crud.crud_se_correspondence import CRUDSECorrespondence
from app.crud.stored_procedures import StoredProcedures
from app.models.se_correspondence import SECorrespondence
from app.schemas.schema_db import SECorrespondenceUpdate
from app.schemas.schema_ms_graph import MessagesSchema, MessageResponseSchema, AttachmentsSchema, \
    SendMessageRequestSchema, UserResponseSchema, MessageSchema, UserSchema
from app.schemas.schema_sp import EmailTrackerGetEmailIDSchema

router = APIRouter()


@router.get("/users/{id}/messages", response_model=MessagesSchema)
async def get_messages(tenant: str, id: str, top: int = 5, filter: str = "") -> MessagesSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        messages: Optional[MessagesSchema] = await MailController.get_messages_while_nextlink(token, tenant, id, top, filter)
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
async def save_message_attachments(tenant: str, id: str, message_id: str, internet_message_id: str = "",
                                   db: Session = Depends(deps.get_mailstore_db)) -> List[str]:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        links = await MailController.save_message_attachments(db, token, id, message_id, internet_message_id)
        if links is None:
            raise HTTPException(status_code=404)
        if len(links) == 0:
            raise HTTPException(status_code=204)
        return links
        # ....
        # attachments_schema: AttachmentsSchema = await MailController.get_message_attachments(token, id, message_id)
        # if attachments_schema is None or attachments_schema.value is None:
        #     # raise HTTPException(status_code=404)
        #     return
        # attachments = attachments_schema.value
        # logger.bind(
        #     message_id=message_id,
        #     attachments="".join([attachment.name for attachment in attachments])
        # ).info("Saving message attachments")
        # links: Optional[List[str]] = await MailController.save_message_attachments_to_disk(db, internet_message_id, attachments)
        # if links is None:
        #     raise HTTPException(status_code=500)  # links is None when mail is not found in db
        # return links
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.get("/users/{id}/messages/{message_id}/saveMessageAndAttachments")
async def save_message_and_attachments(
        tenant: str,
        id: str,
        message_id: str,
        db_fit: Session = Depends(deps.get_fit_db),
        db_mailstore: Session = Depends(deps.get_mailstore_db),
):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        se_correspondence_rows, links = await MailController.save_message_and_attachments(token, tenant, id, message_id, db_fit, db_mailstore)
        return se_correspondence_rows, links
        # .....
        # req_epoch: str = str(int(time.time()))
        # # get messages
        # message_response_schema: Optional[MessageResponseSchema] = await MailController.get_message(token, id, message_id)
        # if message_response_schema is None:
        #     raise HTTPException(status_code=404, detail="No messages found")
        # message = MessageSchema(**(message_response_schema.dict()))
        # # get user
        # user_dict:  Optional[UserResponseSchema] = await UserController.get_user(token, id)  # TODO: Write UserController.get_user
        # if user_dict is None:
        #     raise HTTPException(status_code=500)
        # user: UserResponseSchema = UserResponseSchema(**user_dict)
        # # save messages
        # se_correspondence_rows: List[SECorrespondence] = \
        #     await MailController.process_and_load_to_db_user_messages(tenant, user, [message], db_fit, db_mailstore, req_epoch)
        # # save attachments
        # links = []
        # # message_links = await save_message_attachments(tenant, id, message.id, message.internetMessageId, db=db_mailstore)
        # message_links = await MailController.save_message_attachments(db_mailstore, token, id, message.id, message.internetMessageId)
        # links.append(",".join(message_links))
        # return se_correspondence_rows, links
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.get("/users/{id}/messagesAndAttachments/save")
async def save_user_messages_and_attachments(
        tenant: str,
        id: str,
        top: int = 5,
        filter="",
        db_fit: Session = Depends(deps.get_fit_db),
        db_mailstore: Session = Depends(deps.get_mailstore_db)
) -> (List[SECorrespondence], List[str]):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        se_correspondence_rows, links = \
            await MailController.save_user_messages_and_attachments(token, tenant, id, db_fit, db_mailstore, top, filter)
        if len(se_correspondence_rows) == 0 and len(links) == 0:
            raise HTTPException(status_code=404)
        # ....
        # req_epoch: str = str(int(time.time()))
        # # get messages
        # messages_schema: Optional[MessagesSchema] = await MailController.get_messages(token, tenant, id, top, filter)
        # messages: Optional[List[MessageSchema]] = None
        # try:
        #     messages = messages_schema.value
        # except Exception as e:
        #     print(e)
        # if messages is None or len(messages) == 0:
        #     raise HTTPException(status_code=204, detail="No messages found")
        # # get user
        # user_dict:  Optional[UserResponseSchema] = await UserController.get_user(token, id)
        # if user_dict is None:
        #     raise HTTPException(status_code=500)
        # user: UserResponseSchema = UserResponseSchema(**user_dict)
        # # save messages
        # logger.bind().info("Saving messages")
        # se_correspondence_rows: List[SECorrespondence] = \
        #     await MailController.process_and_load_to_db_user_messages(tenant, user, messages, db_fit, db_mailstore, req_epoch)
        # # save attachments
        # logger.bind().info("Saving messages attachments")
        # links = []
        # for message in messages:
        #     if message.hasAttachments:
        #         logger.bind(message_unique_id=message.internetMessageId).debug("Has attachment(s)")
        #         message_links = await MailController.save_message_attachments(db_mailstore, token, id, message.id, message.internetMessageId)
        #         links.append(",".join(message_links))
        # return se_correspondence_rows, links
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.get("/messagesAndAttachments/save")
async def save_tenant_messages_and_attachments(
        tenant: str,
        top: int = 5,
        filter="",
        db_sales97: Session = Depends(deps.get_sales97_db),
        db_fit: Session = Depends(deps.get_fit_db),
        db_mailstore: Session = Depends(deps.get_mailstore_db)
) -> (List[UserSchema], List[SECorrespondence], List[str]):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        users, all_rows, all_links = \
            await MailController.save_tenant_messages_and_attachments(token, tenant, db_sales97, db_fit, db_mailstore, top, filter)
        return users, all_rows, all_links
        # # get list of trackable users
        # users_to_track: List[EmailTrackerGetEmailIDSchema] = await StoredProcedures.dhruv_EmailTrackerGetEmailID(db_sales97)
        # # get user ids for those email ids
        # users: List[UserSchema] = []
        # for user_to_track in users_to_track:
        #     user = await UserController.get_user_by_email(token, user_to_track.EMailId, "")
        #     if user is None:
        #         logger.bind(user_to_track=user_to_track).error("Cannot find in Azure")
        #     else:
        #         logger.bind(user_to_track=user_to_track).debug("Found in Azure")
        #         users.append(user)
        # # call save_user_messages for each user id
        # all_rows = []
        # all_links = []
        # for user in users:
        #     try:
        #         rows, links = \
        #             await MailController.save_user_messages(token, tenant, user.id, db_fit, db_mailstore, top, filter)
        #         # rows, links = await save_user_messages(tenant, user.id, top, filter, db_fit, db_mailstore)
        #         logger.bind(tenant=tenant, user=user, rows=len(rows), links=len(links)).info("Saved user messages")
        #         if len(rows) > 0: all_rows.append(rows)
        #         if len(links) > 0: all_links.append(",".join(links))
        #     except Exception as e:
        #         logger.bind(
        #             error=token.get("error"),
        #             error_description=token.get("error_description"),
        #             correlation_id=token.get("correlation_id")
        #         ).error(f"investigate:\n {e}")
        #         continue
        # return users, all_rows, all_links
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.get("/messages1/update")
async def update_tenant_messages(
        tenant: str,
        skip: int = 0,
        limit: int = 100,
        db_mailstore: Session = Depends(deps.get_mailstore_db)
) -> List[SECorrespondenceUpdate]:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        se_correspondence_update: List[SECorrespondenceUpdate] = \
            await MailController.update_tenant_messages(token, tenant, db_mailstore, skip, limit)
        return se_correspondence_update
        # .....
        # # get some rows that have empty CorrespondenceId44
        # se_correspondence_rows: List[SECorrespondence] = \
        #     CRUDSECorrespondence(SECorrespondence).get_where_conversation_id_44_is_empty(db_mailstore, skip=skip, limit=limit)
        # # fetch CorrespondenceId for internetMessageId(MailUniqueId)
        # se_correspondence_updates: List[SECorrespondenceUpdate] = []
        # for se_correspondence_row in se_correspondence_rows:
        #     emails = []
        #     if se_correspondence_row.MailFrom: emails.append(se_correspondence_row.MailFrom)
        #     if se_correspondence_row.MailTo: [emails.append(email) for email in se_correspondence_row.MailTo.split(',')]
        #     if se_correspondence_row.MailCC: [emails.append(email) for email in se_correspondence_row.MailCC.split(',')]
        #     if se_correspondence_row.MailBCC: [emails.append(email) for email in se_correspondence_row.MailBCC.split(',')]
        #     user: Optional[UserSchema]
        #     for email in emails:
        #         # get user from email
        #         user = await UserController.get_user_by_email(token, email, "")
        #         if user is None or user.id == "":
        #             continue
        #         # get message for a user and a given message_id
        #         get_messages_filter = f"internetMessageId eq '{se_correspondence_row.MailUniqueId}'"
        #         messages_schema: MessagesSchema = await MailController.get_messages(token, tenant, user.id, 5, get_messages_filter)
        #         if len(messages_schema.value) == 0:
        #             continue
        #         message = messages_schema.value[0]
        #         # create obj for se_correspondence update
        #         se_correspondence_update = SECorrespondenceUpdate(
        #             SeqNo=se_correspondence_row.SeqNo,
        #             ConversationId=message.conversationId,
        #             ConversationId44=message.conversationId[:44]
        #         )
        #         se_correspondence_updates.append(se_correspondence_update)
        #         # update SECorrespondence # TODO: move out of loop to process whole list instead of 1 by 1
        #         update = CRUDSECorrespondence(SECorrespondence).update_conversation_id(
        #             db_mailstore,
        #             se_correspondence_update=se_correspondence_update
        #         )
        #         se_correspondence_updates.append(update)
        #         break
        #     # return users_schema
        # return se_correspondence_updates
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.post("/users/{id}/sendMail", status_code=202)
async def send_mail(tenant: str, id: str, message: SendMessageRequestSchema):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        result = MailController.send_mail(token, id, message)
        return result
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)
