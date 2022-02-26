
from app.apiclients.endpoint_ms import MsEndpointHelper
from app.core.auth import get_ms_auth_config

# def get_s3_path_from_ms_message_id(db: Session, message_id: str) -> str:
#     """
#     gets the record from id table and uses id filed value to get dir_path
#     :param db: Session
#     :param message_id: str
#     :return: str
#     """
#     id_record = CRUDCorrespondenceId(CorrespondenceId).get_by_message_id(db, message_id=message_id)
#     if id_record is None:
#         id_record = CRUDCorrespondenceId(CorrespondenceId).create(
#             db, obj_in=CorrespondenceIdCreate(message_id=message_id))
#     directory = get_s3_path_from_correspondence_id(id_record.id)
#     return directory


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
        # to_add = f"not contains(from/emailAddress/address,'{domain}')"
        to_add = "not contains(from/emailAddress/address,'"+domain+"')"
        new_filter = MsEndpointHelper.build_filter(new_filter, to_add=to_add)
    return new_filter
