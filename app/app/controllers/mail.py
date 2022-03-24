import base64
import time
from datetime import datetime
from io import BytesIO
from typing import Any, Optional, List, Tuple

from aiohttp import ClientResponse
from loguru import logger
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.apiclients.api_client import ApiClient
from app.apiclients.endpoint_ms import MsEndpointHelper, MsEndpointsHelper, endpoints_ms
from app.apiclients.file_client import FileHelper
from app.controllers.user import UserController
# from app.core.auth import get_ms_auth_config, MsAuthConfig
from app.core.config import configuration, MailIntegrateJobDependency, AzureAuth
from app.crud.crud_se_correspondence import CRUDSECorrespondence
from app.crud.stored_procedures import StoredProcedures
from app.models.se_correspondence import SECorrespondence
from app.schemas.schema_db import SECorrespondenceCreate, SECorrespondenceUpdate
from app.schemas.schema_ms_graph import MessageResponseSchema, MessageSchema, MessagesSchema, AttachmentsSchema, \
    AttachmentSchema, UserResponseSchema, SendMessageRequestSchema, UserSchema
from app.schemas.schema_sp import EmailTrackerGetEmailLinkInfo, EmailTrackerGetEmailLinkInfoParams


class MailController:

    @staticmethod
    async def get_messages(token: Any, tenant: str, user_id: str, top: int, filter: str) -> Optional[MessagesSchema]:
        """
        Queries msgraph to get messages

        :param token: Any
        :param tenant: str
        :param user_id: str
        :param top: int
        :param filter: str
        :return: Optional[MessagesSchema]
        """
        endpoint = MsEndpointsHelper.get_endpoint("message:list", endpoints_ms)
        endpoint.request_params['id'] = user_id
        endpoint.optional_query_params.top = str(top) if 0 < top <= 1000 else str(10)
        new_filter = filter  # add_filter_to_leave_out_internal_domain_messages(tenant, filter)
        if new_filter != "":
            endpoint.optional_query_params.filter = new_filter
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=30)
        response, data = await api_client.retryable_call()
        try:
            return MessagesSchema(**data)
        except Exception as e:
            logger.bind(data=data).error("Error in converting dict to MessagesSchema")

    @staticmethod
    async def get_messages_while_nextlink(token: Any, tenant: str, user_id: str, top: int, filter: str) -> List[MessageSchema]:
        """
        Continuously queries in msgraph for messages

        :param token: Any
        :param tenant: str
        :param user_id: str
        :param top: int
        :param filter: str
        :return: List[MessageSchema]
        """
        # messages: List[MessageSchema] = []
        messages_schema: Optional[MessagesSchema] = await MailController.get_messages(token, tenant, user_id, top, filter)
        messages = messages_schema.value
        while messages_schema.odata_nextLink:
            api_client = ApiClient('get', messages_schema.odata_nextLink, headers=ApiClient.get_headers(token), timeout_sec=30)
            response, data = await api_client.retryable_call()
            messages_schema = MessagesSchema(**data)
            messages.extend(messages_schema.value)

        return messages

    @staticmethod
    async def get_message(token: Any, user_id: str, message_id: str) -> Optional[MessageResponseSchema]:
        """
        Query msgraph to get message for a messageId

        :param token: Any
        :param user_id: str
        :param message_id: str
        :return: Optional[MessageResponseSchema]
        """
        endpoint = MsEndpointsHelper.get_endpoint("message:get", endpoints_ms)
        endpoint.request_params["id"] = user_id
        endpoint.request_params["message_id"] = message_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=30)
        response, data = await api_client.retryable_call()
        return MessageResponseSchema(**data) if type(data) == dict else data

    # @staticmethod # use save_messages: use a list
    # async def save_message(message: MessageSchema):
    #     pass

    @staticmethod
    async def process_and_save_user_messages(
            tenant: str,
            user: UserResponseSchema,
            messages: List[MessageSchema],
            db_fit: Session,
            db_mailstore: Session,
            process_ind: str
    ) -> List[SECorrespondence]:
        """
        Process messages for user and save to mailstore

        :param tenant: str
        :param user: UserResponseSchema
        :param messages: List[MessageSchema]
        :param db_fit: Session
        :param db_mailstore: Session
        :param process_ind: str
        :return: List[SECorrespondence]
        """
        processed_messages: List[SECorrespondenceCreate] = await MailProcessor.process_messages(
            tenant, user, messages, db_fit, db_mailstore, process_ind
        )
        se_correspondence_rows = CRUDSECorrespondence(SECorrespondence)\
            .get_by_mail_unique_id_or_create_get_if_not_exist_multi(db_mailstore, obj_ins=processed_messages)
        return se_correspondence_rows

    @staticmethod
    async def save_user_messages_and_attachments(
            token: any,
            tenant: str,
            id: str,
            db_fit: Session,
            db_mailstore: Session,
            top: int = 5,
            filter: str = "",
    ) -> (List[SECorrespondence], List[str]):
        """
        Save user messages and attachments

        :param token: Any
        :param tenant: str
        :param id: str
        :param db_fit: Session
        :param db_mailstore: Session
        :param top: int
        :param filter: str
        :return: (List[SECorrespondence], List[str])
        """
        req_epoch: str = str(int(time.time()))
        messages: List[MessageSchema] = await MailController.get_messages_while_nextlink(token, tenant, id, top, filter)
        if messages is None or len(messages) == 0:
            logger.bind().error("no messages")
            return None
        # get user
        user: Optional[UserResponseSchema] = await UserController.get_user(token, id)
        if user is None:
            logger.bind().error("no user")
            return None
        # save messages
        logger.bind().info("Saving messages")
        se_correspondence_rows: List[SECorrespondence] = await MailController.process_and_save_user_messages(
            tenant, user, messages, db_fit, db_mailstore, req_epoch
        )
        # save attachments
        links: List[str] = await MailController.process_and_save_user_messages_attachments_to_disk(
            token, tenant, id, messages, db_mailstore
        )
        return se_correspondence_rows, links

    @staticmethod
    async def get_message_attachments(token: Any, user_id: str, message_id: str) -> AttachmentsSchema:
        """
        Get message attachments from msgraph

        :param token: Any
        :param user_id: str
        :param message_id: str
        :return: AttachmentsSchema
        """
        endpoint = MsEndpointsHelper.get_endpoint("message:list:attachment", endpoints_ms)
        endpoint.request_params["id"] = user_id
        endpoint.request_params["message_id"] = message_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=30)
        response, data = await api_client.retryable_call()
        try:
            return AttachmentsSchema(**data)
        except Exception as e:
            logger.bind().error(e)

    @staticmethod
    async def save_message_attachments(
            tenant: str, db_mailstore: Session, token: Any, user_id: str, message_id: str, internet_message_id: str
    ) -> Optional[List[str]]:
        """
        Save message attachments to disk if message is present in db

        :param tenant str
        :param db_mailstore: Session
        :param token: Any
        :param user_id: str
        :param message_id: str
        :param internet_message_id: str
        :return: Optional[List[str]]
        """
        attachments_schema: AttachmentsSchema = await MailController.get_message_attachments(token, user_id, message_id)
        if attachments_schema is None or attachments_schema.value is None:
            return None
        attachments = attachments_schema.value
        links: Optional[List[str]] = await MailController.save_attachments_to_disk_if_message_in_db(
            tenant,
            db_mailstore,
            internet_message_id,
            attachments
        )
        logger.bind(
            mail_unique_id=internet_message_id, attachments="".join([attachment.name for attachment in attachments])
        ).info("Saved message attachments to disk")
        return links

    @staticmethod
    async def save_attachments_to_disk_if_message_in_db(tenant: str, db_mailstore: Session, internet_message_id: str, attachments: List[AttachmentSchema]) -> Optional[List[str]]:
        """
        Save message attachments to disk if message is present in db

        :param tenant: str
        :param db_mailstore:
        :param internet_message_id:
        :param attachments:
        :return:
        """
        correspondence: Optional[SECorrespondence] = await MailController.get_mail_from_db(internet_message_id, db_mailstore)
        if correspondence is None:
            return None
        links = []
        for attachment in attachments:
            if attachment.contentBytes is None:
                logger.bind(internet_message_id=internet_message_id, attachment=attachment.name).error("Message attachment has no content")
                continue
            content_b64 = attachment.contentBytes
            # contentBytes is base64 encoded str
            content = base64.b64decode(content_b64)
            filename = attachment.name
            file_relative_path = get_attachments_path_from_id(correspondence.SeqNo)
            saved_to = await FileHelper.get_or_save_get_in_disk(
                BytesIO(content),
                configuration.tenant_configurations.get(tenant).disk.disk_base_path,
                file_relative_path,
                filename
            )
            logger.bind(saved_to=saved_to).info("Saved to disk")
            links.append(saved_to)
        return links

    @staticmethod
    async def process_and_save_user_messages_attachments_to_disk(token:Any, tenant: str, id: str, messages: List[MessageSchema], db_mailstore: Session) -> List[str]:
        """
        Process and save user messages-attachments to disk

        :param token: Any
        :param tenant: str
        :param id: str
        :param messages: List[MessageSchema]
        :param db_mailstore: Session
        :return: List[str]
        """
        links: List[str] = []
        for message in messages:
            if not message.hasAttachments:
                logger.bind(message_unique_id=message.internetMessageId).debug("Mail has no attachment(s)")
                continue
            if await MailController.get_mail_from_db(message.internetMessageId, db_mailstore) is None:
                logger.bind(internet_message_id=message.internetMessageId).debug("Mail Not found in db")
                continue
            message_links = await MailController.save_message_attachments(tenant, db_mailstore, token, id, message.id, message.internetMessageId)
            if message_links is None:
                logger.bind().debug("No attachment saved")
                continue
            links.append(",".join(message_links))
            return links

    @staticmethod
    async def get_mail_from_db(internet_message_id: str, db_mailstore: Session) -> Optional[SECorrespondence]:
        """

        :param internet_message_id: str
        :param db_mailstore: Session
        :return: Optional[SECorrespondence]
        """
        correspondence: Optional[SECorrespondence] = \
            CRUDSECorrespondence(SECorrespondence).get_by_mail_unique_id(db_mailstore, mail_unique_id=internet_message_id)
        if correspondence is None:
            return None  # no row in db
        return correspondence

    @staticmethod
    async def save_message_and_attachments(
            token: Any,
            tenant: str,
            id: str,
            message_id: str,
            db_fit: Session,
            db_mailstore: Session
    ):
        req_epoch: str = str(int(time.time()))
        # get messages
        message_response_schema: Optional[MessageResponseSchema] = await MailController.get_message(token, id, message_id)
        if message_response_schema is None:
            logger.bind().error("Could not find message")
            return None
        message = MessageSchema(**(message_response_schema.dict()))
        # get user
        user_dict:  Optional[UserResponseSchema] = await UserController.get_user(token, id)  # TODO: Write UserController.get_user
        if user_dict is None:
            logger.bind().error("Could not find user")
            return None
        user: UserResponseSchema = UserResponseSchema(**user_dict)
        # save messages
        se_correspondence_rows: List[SECorrespondence] = \
            await MailController.process_and_save_user_messages(tenant, user, [message], db_fit, db_mailstore, req_epoch)
        # save attachments
        links = []
        message_links = await MailController.save_message_attachments(tenant, db_mailstore, token, id, message.id, message.internetMessageId)
        links.append(",".join(message_links))
        return se_correspondence_rows, links

    @staticmethod
    async def save_tenant_messages_and_attachments(
            token: Any,
            tenant: str,
            db_sales97: Session,
            db_fit: Session,
            db_mailstore: Session,
            top: int = 5,
            filter: str = ""
    ) -> (List[UserSchema], List[SECorrespondence], List[str]):
        # get list of trackable users
        users: List[UserSchema] = await UserController.get_users_to_track(token, db_sales97)
        # call save_user_messages for each user id
        all_rows = []
        all_links = []
        for user in users:
            try:
                rows, links = \
                    await MailController.save_user_messages_and_attachments(token, tenant, user.id, db_fit, db_mailstore, top, filter)
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

    @staticmethod
    async def update_tenant_messages(
            token: Any, tenant: str, db_mailstore: Session, skip: int = 0, limit: int = 100
    ) -> List[SECorrespondenceUpdate]:
        # get some rows that have empty CorrespondenceId44
        se_correspondence_rows: List[SECorrespondence] = \
            CRUDSECorrespondence(SECorrespondence).get_where_conversation_id_44_is_empty(db_mailstore, skip=skip, limit=limit)
        # fetch CorrespondenceId for internetMessageId(MailUniqueId)
        se_correspondence_updates: List[SECorrespondenceUpdate] = []
        for se_correspondence_row in se_correspondence_rows:
            emails = []
            if se_correspondence_row.MailFrom: emails.append(se_correspondence_row.MailFrom)
            if se_correspondence_row.MailTo: [emails.append(email) for email in se_correspondence_row.MailTo.split(',')]
            if se_correspondence_row.MailCC: [emails.append(email) for email in se_correspondence_row.MailCC.split(',')]
            if se_correspondence_row.MailBCC: [emails.append(email) for email in se_correspondence_row.MailBCC.split(',')]
            user: Optional[UserSchema]
            for email in emails:
                # get user from email
                user = await UserController.get_user_by_email(token, email, "")
                if user is None or user.id == "":
                    continue
                # get message for a user and a given message_id
                get_messages_filter = f"internetMessageId eq '{se_correspondence_row.MailUniqueId}'"
                messages_schema: MessagesSchema = await MailController.get_messages(token, tenant, user.id, 5, get_messages_filter)
                if messages_schema is None:
                    logger.bind(
                        tenant=tenant, user_email=email, mail_subject=se_correspondence_row.MailSubject
                    ).error("messages_schema is None, skipping this record")
                    continue
                if len(messages_schema.value) == 0:
                    continue
                message = messages_schema.value[0]
                # create obj for se_correspondence update
                se_correspondence_update = SECorrespondenceUpdate(
                    SeqNo=se_correspondence_row.SeqNo,
                    ConversationId=message.conversationId,
                    ConversationId44=message.conversationId[:44]
                )
                se_correspondence_updates.append(se_correspondence_update)
                # update SECorrespondence # TODO: move out of loop to process whole list instead of 1 by 1
                update = CRUDSECorrespondence(SECorrespondence).update_conversation_id(
                    db_mailstore,
                    se_correspondence_update=se_correspondence_update
                )
                se_correspondence_updates.append(update)
                break
            # return users_schema
        return se_correspondence_updates

    @staticmethod
    async def send_mail(token: Any, user_id: str, message: SendMessageRequestSchema):
        message: SendMessageRequestSchema = \
            map_inplace_SendMessageRequestSchema_to_msgrapgh_SendMessageRequestSchema(message)
        endpoint = MsEndpointsHelper.get_endpoint("message:send", endpoints_ms)
        endpoint.request_params["id"] = user_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(
            endpoint.request_method,
            url,
            headers=ApiClient.get_headers(token),
            data=message.json(),
            timeout_sec=3000)
        api_client.headers['content-type'] = "application/json"
        response_and_data: Tuple[ClientResponse, str] = await api_client.retryable_call()
        response, data = response_and_data
        return JSONResponse(status_code=response.status, content={"message": data})

class MailProcessor:

    @staticmethod
    async def process_messages(
            tenant: str,
            user: UserResponseSchema,
            messages: List[MessageSchema],
            db_fit: Session,
            db_mailstore: Session,
            process_ind: str
    ) -> List[SECorrespondenceCreate]:
        """

        :param tenant: str
        :param user: UserResponseSchema
        :param messages: List[MessageSchema]
        :param db_fit: Session
        :param db_mailstore: Session
        :param process_ind: str
        :return: List[SECorrespondenceCreate]
        """
        se_correspondence_create_schemas: List[SECorrespondenceCreate] = []
        for message in messages:
            obj_in: Optional[SECorrespondenceCreate] = await MailProcessor.process_message(
                tenant, user, message, db_fit, db_mailstore, process_ind
            )
            if obj_in is not None:
                se_correspondence_create_schemas.append(obj_in)
        return se_correspondence_create_schemas

    @staticmethod
    async def process_message(
            tenant: str,
            user: UserResponseSchema,
            message: MessageSchema,
            db_fit: Session,
            db_mailstore: Session,
            process_time: str = str(int(time.time()))
    ) -> Optional[SECorrespondenceCreate]:
        obj_in: Optional[SECorrespondenceCreate] = None
        if message.from_email is None:
            return None
        if MailProcessor.is_outgoing(user, message):
            to_addresses: List[str] = [recipient.emailAddress.address for recipient in message.toRecipients]
            for to_address in to_addresses:
                # process message only if it is related to a client
                if not MailProcessor.is_internal_address(tenant, to_address):
                    obj_in: Optional[SECorrespondenceCreate] = await MailProcessor.process_or_discard_message(
                        tenant, to_address, message, db_fit, db_mailstore, process_time
                    )
                    if obj_in is not None:
                        break
        else:  # incoming email
            from_address = message.from_email.emailAddress.address
            # process message only if it is related to a client
            if not MailProcessor.is_internal_address(tenant, from_address):
                obj_in: Optional[SECorrespondenceCreate] = \
                    await MailProcessor.process_or_discard_message(
                        tenant, from_address, message, db_fit, db_mailstore, process_time
                    )
        return obj_in

    @staticmethod
    async def process_or_discard_message(
            tenant: str,
            email_address: str,
            message: MessageSchema,
            db_fit: Session,
            db_mailstore: Session,
            process_time: str = str(int(time.time()))
    ) -> Optional[SECorrespondenceCreate]:
        obj_in: Optional[SECorrespondenceCreate] = None
        if not MailProcessor.is_internal_address(tenant, email_address):
            # logger.bind(email=email_address, message=message.id).debug("process_or_discard_message")
            # get email_link_info
            email_link_info: EmailTrackerGetEmailLinkInfo = await MailProcessor.get_email_link_from_dhruv(
                email_address, message.sentDateTime, message.conversationId, db_fit
            )
            # get is_email_chain_origin
            is_mail_chain_origin_in_dhruv: bool = await MailProcessor.is_mail_chain_origin_in_dhruv(
                db_mailstore, message.from_email.emailAddress.address, message.subject
            )

            obj_in: Optional[SECorrespondenceCreate] = None
            dependencies = configuration.tenant_configurations.get(tenant).mail_integrate_job.dependencies
            is_check_DhruvOrigin: bool = MailIntegrateJobDependency.DhruvOrigin in dependencies
            is_check_EmailLink: bool = MailIntegrateJobDependency.EmailLink in dependencies
            if is_check_EmailLink and is_check_DhruvOrigin:
                # check if we can process message
                if len(email_link_info.AccountCode) > 0 or is_mail_chain_origin_in_dhruv:
                    # process
                    logger.bind(
                        dependencies=dependencies, email=email_address,
                        message=message.internetMessageId, subject=message.subject).info("processed message")
                    obj_in = map_MessageSchema_to_SECorrespondenceCreate(
                        message, email_link_info, process_time
                    )
                else:
                    logger.bind(
                        message_internetMessageId=message.internetMessageId, message_subject=message.subject
                    ).error("Discarding message")
            elif is_check_EmailLink and not is_check_DhruvOrigin:
                # check if we can process message
                if len(email_link_info.AccountCode) > 0:
                    # process
                    logger.bind(
                        dependencies=dependencies, email=email_address,
                        message=message.internetMessageId, subject=message.subject).info("processed message")
                    obj_in = map_MessageSchema_to_SECorrespondenceCreate(
                        message, email_link_info, process_time
                    )
            elif not is_check_EmailLink and is_check_DhruvOrigin:
                # check if we can process message
                if is_mail_chain_origin_in_dhruv:
                    # process
                    logger.bind(
                        dependencies=dependencies,email=email_address,
                        message=message.internetMessageId, subject=message.subject).info("processed message")
                    obj_in = map_MessageSchema_to_SECorrespondenceCreate(
                        message, email_link_info, process_time
                    )
        return obj_in

    @staticmethod
    async def get_email_link_from_dhruv(email: str, date: str, conversation_id: str, db: Session) -> EmailTrackerGetEmailLinkInfo:
        # get email link info from dhruv
        email_link_info_params = EmailTrackerGetEmailLinkInfoParams(email=email, date=date, conversation_id=conversation_id)
        email_links_info = \
            await StoredProcedures.dhruv_EmailTrackerGetEmailLinkInfo(db, email_link_info_params)
        return email_links_info[0]

    @staticmethod
    def is_outgoing(user: UserResponseSchema, message: MessageSchema) -> bool:
        try:
            if message.from_email is not None:
                return user.mail == message.from_email.emailAddress.address
            else:
                return False
        except Exception as e:
            print(f"TODO: investigate, \n{e}")

    @staticmethod
    def is_internal_address(tenant: str, address: str) -> bool:
        tenant_config: AzureAuth = configuration.get_ms_auth_config(tenant)
        for domain in tenant_config.internal_domains:
            if domain.lower() in address.lower(): return True
        return False

    @staticmethod
    def is_external_address(tenant: str, address: str) -> bool:
        return not MailProcessor.is_internal_address(tenant, address)

    @staticmethod
    async def is_mail_chain_origin_in_dhruv(db: Session, from_address: str, subject: str) -> bool:
        is_origin_dhruv = CRUDSECorrespondence(SECorrespondence).is_mail_chain_origin_in_dhruv(
            db, from_address=from_address, subject=subject
        )
        return is_origin_dhruv is not None


def get_attachments_path_from_id(id: int, *, min_length=6) -> str:
    """
    converts int to str of min_length and then splits each digit with "/"
    :param id:
    :param min_length:
    :return: str
    """
    if id <= 0:
        return ""
    id_str = str(id)
    if len(id_str) < min_length:
        concat_str = "".join(['0' for i in range(0, min_length-len(id_str))])
        id_str = concat_str+id_str

    path = "/".join([id_str[i] for i in range(0, len(id_str))])
    path = f"{path}/{id}"
    return path


def add_filter_to_leave_out_internal_domain_messages(tenant_id: str, filter: str) -> str:
    # tenant_ms_auth_config = get_ms_auth_config(tenant_id)
    tenant_ms_auth_config = configuration.get_ms_auth_config(tenant_id)
    internal_domains: list = tenant_ms_auth_config.internal_domains
    new_filter = filter
    for domain in internal_domains:
        to_add = f"not contains(from/emailAddress/address,'{domain}')"
        # to_add = "not contains(from/emailAddress/address,'"+domain+"')"
        new_filter = MsEndpointHelper.build_filter(new_filter, to_add=to_add)
    return new_filter


def map_MessageSchema_to_SECorrespondenceCreate(
        message: MessageSchema,
        email_link_info: EmailTrackerGetEmailLinkInfo,
        loop_start_epoch: str
) -> SECorrespondenceCreate:
    curr_date_time: datetime = datetime.fromisoformat(datetime.utcnow().isoformat(sep='T', timespec='seconds'))
    obj_in = SECorrespondenceCreate(
        DocSentDate=datetime.strptime(message.sentDateTime, "%Y-%m-%dT%H:%M:%SZ"),
        MailUniqueId=message.internetMessageId,
        MailSubject=message.subject,
        MailBody1=message.body.content,
        MailTo=",".join([toRecipient.emailAddress.address for toRecipient in message.toRecipients]),
        MailCC="",
        MailFrom=message.from_email.emailAddress.address,
        MailBCC="",
        DocSendOn=datetime.strptime(message.sentDateTime, "%Y-%m-%dT%H:%M:%SZ"),
        QuoteNo=email_link_info.QuoteNo,
        BkgNo=email_link_info.BkgNo,
        AccountCode=email_link_info.AccountCode,
        IsAttachmentProcessed=False,
        HasAttachment=message.hasAttachments,
        ConversationId=message.conversationId,
        ConversationId44=message.conversationId[:44],

        CrDate=curr_date_time,
        CrTime=curr_date_time,
        UpdDate=curr_date_time,
        UpdTime=curr_date_time,
        UpdPlace=loop_start_epoch,
    )
    return obj_in


def map_inplace_SendMessageRequestSchema_to_msgrapgh_SendMessageRequestSchema(message: SendMessageRequestSchema):
    attachments: List[dict] = []
    if message.message.attachments and len(message.message.attachments) > 0:
        for attachment in message.message.attachments:
            # NOTE: Converting to dict for field '@odata.type'
            attachment_dict = {
                '@odata.type': attachment.odata_type,
                'name': attachment.name,
                'contentType': attachment.contentType,
                'contentBytes': attachment.contentBytes
            }
            attachments.append(attachment_dict)
    message.message.attachments = attachments
    return message
