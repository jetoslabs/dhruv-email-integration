import base64
import time
from datetime import datetime
from io import BytesIO
from typing import Any, Optional, List

from loguru import logger
from sqlalchemy.orm import Session

from app.api.api_v1.endpoints.users import get_user
from app.apiclients.api_client import ApiClient
from app.apiclients.endpoint_ms import MsEndpointHelper, MsEndpointsHelper, endpoints_ms
from app.apiclients.file_client import FileHelper
from app.core.auth import get_ms_auth_config, MsAuthConfig
from app.core.config import global_config
from app.crud.crud_se_correspondence import CRUDSECorrespondence
from app.crud.stored_procedures import StoredProcedures
from app.models.se_correspondence import SECorrespondence
from app.schemas.schema_db import SECorrespondenceCreate
from app.schemas.schema_ms_graph import MessageResponseSchema, MessageSchema, MessagesSchema, AttachmentsSchema, \
    AttachmentSchema, UserResponseSchema
from app.schemas.schema_sp import EmailTrackerGetEmailLinkInfo, EmailTrackerGetEmailLinkInfoParams


class MailController:

    @staticmethod
    async def get_messages(token: Any, tenant: str, user_id: str, top: int, filter: str) -> Optional[MessagesSchema]:
        endpoint = MsEndpointsHelper.get_endpoint("message:list", endpoints_ms)
        endpoint.request_params['id'] = user_id
        endpoint.optional_query_params.top = str(top) if 0 < top <= 1000 else str(10)
        new_filter = add_filter_to_leave_out_internal_domain_messages(tenant, filter)
        if new_filter != "":
            endpoint.optional_query_params.filter = new_filter
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=30)
        response, data = await api_client.retryable_call()
        try:  # TODO: remove try catch
            return MessagesSchema(**data) if type(data) == dict else data
        except Exception as e:
            logger.bind().error(e)

    # @staticmethod # use save_messages: use a list
    # async def save_message(message: MessageSchema):
    #     pass

    @staticmethod
    async def save_user_messages(
            tenant: str,
            user: UserResponseSchema,
            messages: List[MessageSchema],
            db_fit: Session,
            db_mailstore: Session,
            process_ind: str
    ):
        processed_messages: List[SECorrespondenceCreate] = await MailProcessor.process_messages(
            tenant, user, messages, db_fit, process_ind
        )
        se_correspondence_rows = CRUDSECorrespondence(SECorrespondence)\
            .get_by_mail_unique_id_or_create_get_if_not_exist_multi(db_mailstore, obj_ins=processed_messages)
        return se_correspondence_rows




    @staticmethod
    async def get_message(token: Any, user_id: str, message_id: str) -> Optional[MessageResponseSchema]:
        endpoint = MsEndpointsHelper.get_endpoint("message:get", endpoints_ms)
        endpoint.request_params["id"] = user_id
        endpoint.request_params["message_id"] = message_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=30)
        response, data = await api_client.retryable_call()
        return MessageResponseSchema(**data) if type(data) == dict else data

    @staticmethod
    async def get_message_attachments(token: Any, user_id: str, message_id: str) -> AttachmentsSchema:
        endpoint = MsEndpointsHelper.get_endpoint("message:list:attachment", endpoints_ms)
        endpoint.request_params["id"] = user_id
        endpoint.request_params["message_id"] = message_id
        url = MsEndpointHelper.form_url(endpoint)
        api_client = ApiClient(endpoint.request_method, url, headers=ApiClient.get_headers(token), timeout_sec=30)
        response, data = await api_client.retryable_call()
        return AttachmentsSchema(**data)

    @staticmethod
    async def save_message_attachments(db_mailstore, message_id: str, attachments: List[AttachmentSchema]) -> Optional[List[str]]:
        correspondence: Optional[SECorrespondence] = \
            CRUDSECorrespondence(SECorrespondence).get_by_mail_unique_id(db_mailstore, mail_unique_id=message_id)
        if correspondence is None:
            logger.bind(message_id=message_id).error("Mail Not found ")
            return None  # no row in db
        links = []
        for attachment in attachments:
            if attachment.contentBytes is None:
                logger.bind(message_id=message_id, attachment=attachment.name).error("Message attachment has no content")
                continue
            content_b64 = attachment.contentBytes
            # contentBytes is base64 encoded str
            content = base64.b64decode(content_b64)

            filename = attachment.name
            file_relative_path = get_attachments_path_from_id(correspondence.SeqNo)
            saved_to = await FileHelper.get_or_save_get_in_disk(
                BytesIO(content), global_config.disk_base_path, file_relative_path, filename
            )
            logger.bind(saved_to=saved_to).info("Saved to disk")
            links.append(saved_to)
        return links


class MailProcessor:

    @staticmethod
    async def process_messages(
            tenant: str,
            user: UserResponseSchema,
            messages: List[MessageSchema],
            db_fit: Session,
            process_ind: str
    ) -> List[SECorrespondenceCreate]:
        se_correspondence_create_schemas: List[SECorrespondenceCreate] = []
        for message in messages:
            obj_in: Optional[SECorrespondenceCreate] = await MailProcessor.process_message(
                tenant, user, message, db_fit, process_ind
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
                        tenant, to_address, message, db_fit, process_time
                    )
                    if obj_in is not None:
                        break
        else:  # incoming email
            from_address = message.from_email.emailAddress.address
            # process message only if it is related to a client
            if not MailProcessor.is_internal_address(tenant, from_address):
                obj_in: Optional[SECorrespondenceCreate] = \
                    await MailProcessor.process_or_discard_message(
                        tenant, from_address, message, db_fit, process_time
                    )
        return obj_in

    @staticmethod
    async def process_or_discard_message(
            tenant: str,
            email_address: str,
            message: MessageSchema,
            db_fit: Session,
            process_time: str = str(int(time.time()))
    ) -> Optional[SECorrespondenceCreate]:
        obj_in: Optional[SECorrespondenceCreate] = None
        if not MailProcessor.is_internal_address(tenant, email_address):
            email_link_info: EmailTrackerGetEmailLinkInfo = await MailProcessor.get_email_link_from_dhruv(
                email_address, message.sentDateTime, db_fit
            )
            if len(email_link_info.AccountCode) > 0:
                obj_in = map_MessageSchema_to_SECorrespondenceCreate(
                    message, email_link_info, process_time
                )
        return obj_in

    @staticmethod
    async def get_email_link_from_dhruv(email: str, date: str, db: Session) -> EmailTrackerGetEmailLinkInfo:
        # get email link info from dhruv
        email_link_info_params = EmailTrackerGetEmailLinkInfoParams(email=email, date=date)
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
    def is_internal_address(tenant: str, address: str):
        tenant_config: MsAuthConfig = get_ms_auth_config(tenant)
        for domain in tenant_config.internal_domains:
            if domain.lower() in address.lower(): return True
        return False

    @staticmethod
    def is_external_address(tenant: str, address: str):
        return not MailProcessor.is_internal_address(tenant, address)

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
    tenant_ms_auth_config = get_ms_auth_config(tenant_id)
    internal_domains: list = tenant_ms_auth_config.internal_domains
    new_filter = filter
    for domain in internal_domains:
        to_add = f"not contains(from/emailAddress/address,'{domain}')"
        # to_add = "not contains(from/emailAddress/address,'"+domain+"')"
        new_filter = MsEndpointHelper.build_filter(new_filter, to_add=to_add)
    return new_filter


def map_MessageResponseSchema_to_SECorrespondenceCreate(
        message: MessageResponseSchema,
        email_link_info: EmailTrackerGetEmailLinkInfo,
        loop_start_epoch: str
) -> SECorrespondenceCreate:
    curr_date_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    obj_in = SECorrespondenceCreate(
        DocSentDate=datetime.strptime(message.sentDateTime, "%Y-%m-%dT%H:%M:%SZ"),
        MailUniqueId=message.id,
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

        CrDate=curr_date_time,
        CrTime=curr_date_time,
        UpdDate=curr_date_time,
        UpdTime=curr_date_time,
        UpdPlace=loop_start_epoch,
    )
    return obj_in


def map_MessageSchema_to_SECorrespondenceCreate(
        message: MessageSchema,
        email_link_info: EmailTrackerGetEmailLinkInfo,
        loop_start_epoch: str
) -> SECorrespondenceCreate:
    curr_date_time: datetime = datetime.fromisoformat(datetime.utcnow().isoformat(sep='T', timespec='seconds'))
    obj_in = SECorrespondenceCreate(
        DocSentDate=datetime.strptime(message.sentDateTime, "%Y-%m-%dT%H:%M:%SZ"),
        MailUniqueId=message.id,
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

        CrDate=curr_date_time,
        CrTime=curr_date_time,
        UpdDate=curr_date_time,
        UpdTime=curr_date_time,
        UpdPlace=loop_start_epoch,
    )
    return obj_in
