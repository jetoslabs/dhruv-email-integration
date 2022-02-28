from datetime import datetime

from app.apiclients.endpoint_ms import MsEndpointHelper
from app.core.auth import get_ms_auth_config
from app.schemas.schema_db import SECorrespondenceCreate
from app.schemas.schema_ms_graph import MessageResponseSchema, MessageSchema
from app.schemas.schema_sp import EmailTrackerGetEmailLinkInfo


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

    return "/".join([id_str[i] for i in range(0, len(id_str))])


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
