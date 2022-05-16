from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.orm import Session

from app.api import deps
from app.controllers.mail import MailController
from app.core.auth import get_auth_config_and_confidential_client_application_and_access_token
from app.models.se_correspondence import SECorrespondence
from app.schemas.schema_db import SECorrespondenceUpdate
from app.schemas.schema_ms_graph import MessagesSchema, MessageResponseSchema, AttachmentsSchema, \
    SendMessageRequestSchema, UserSchema, MessageSchema

router = APIRouter()


@router.get("/users/{id}/messages", response_model=List[MessageSchema])
async def get_messages(
        tenant: str, id: str, top: int = 5, filter: str = "", _=Depends(deps.assert_tenant)
) -> MessagesSchema:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        messages: List[MessageSchema] = await MailController.get_messages_while_nextlink(token, tenant, id, top, filter)
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
async def get_message(
        tenant: str, id: str, message_id: str, _=Depends(deps.assert_tenant)
) -> MessageResponseSchema:
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
async def list_message_attachments(
        tenant: str, id: str, message_id: str, _=Depends(deps.assert_tenant)
) -> AttachmentsSchema:
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
        tenant: str,
        id: str,
        message_id: str,
        internet_message_id: str = "",
        _=Depends(deps.assert_tenant),
        db: Session = Depends(deps.get_tenant_mailstore_db)
) -> List[str]:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        links = await MailController.save_message_attachments(tenant, db, token, id, message_id, internet_message_id)
        if links is None:
            raise HTTPException(status_code=404)
        if len(links) == 0:
            raise HTTPException(status_code=204)
        return links
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
        _=Depends(deps.assert_tenant),
        db_fit: Session = Depends(deps.get_tenant_fit_db),
        db_mailstore: Session = Depends(deps.get_tenant_mailstore_db),
):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        se_correspondence_rows, links = await MailController.save_message_and_attachments(token, tenant, id, message_id,
                                                                                          db_fit, db_mailstore)
        return se_correspondence_rows, links
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
        _=Depends(deps.assert_tenant),
        db_fit: Session = Depends(deps.get_tenant_fit_db),
        db_mailstore: Session = Depends(deps.get_tenant_mailstore_db)
) -> (List[SECorrespondence], List[str]):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        se_correspondence_rows, links = \
            await MailController.save_user_messages_and_attachments(token, tenant, id, db_fit, db_mailstore, top,
                                                                    filter)
        return se_correspondence_rows, links
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
        _=Depends(deps.assert_tenant),
        db_sales97: Session = Depends(deps.get_tenant_sales97_db),
        db_fit: Session = Depends(deps.get_tenant_fit_db),
        db_mailstore: Session = Depends(deps.get_tenant_mailstore_db)
) -> (List[UserSchema], List[SECorrespondence], List[str]):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        users, all_rows, all_links = \
            await MailController.save_tenant_messages_and_attachments(token, tenant, db_sales97, db_fit, db_mailstore,
                                                                      top, filter)
        return users, all_rows, all_links
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
        _=Depends(deps.assert_tenant),
        # db_mailstore: Session = Depends(deps.get_mailstore_db)
        db_mailstore: Session = Depends(deps.get_tenant_mailstore_db)
) -> List[SECorrespondenceUpdate]:
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        se_correspondence_update: List[SECorrespondenceUpdate] = \
            await MailController.update_tenant_messages(token, tenant, db_mailstore, skip, limit)
        return se_correspondence_update
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)


@router.post("/users/{id}/sendMail", status_code=202)
async def send_mail(tenant: str, id: str, message: SendMessageRequestSchema, _=Depends(deps.assert_tenant)):
    config, client_app, token = get_auth_config_and_confidential_client_application_and_access_token(tenant)
    if "access_token" in token:
        result = await MailController.send_mail(token, id, message)
        return result
    else:
        logger.bind(
            error=token.get("error"),
            error_description=token.get("error_description"),
            correlation_id=token.get("correlation_id")
        ).error("Unauthorized")
        raise HTTPException(status_code=401)
