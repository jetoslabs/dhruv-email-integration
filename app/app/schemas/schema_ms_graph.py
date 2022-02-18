from datetime import time
from typing import List, Optional, Any

from pydantic import BaseModel, Field


class ODataContextSchema(BaseModel):
    odata_context: str = Field(None, alias="@odata.context")


class ODataNextLinkSchema(BaseModel):
    odata_nextLink: str = Field(None, alias="@odata.nextLink")


class UserSchema(BaseModel):
    businessPhones: Optional[List[str]] = None
    displayName: Optional[str]
    givenName: Optional[str]
    jobTitle: Optional[str]
    mail: Optional[str]
    mobilePhone: Optional[str]
    officeLocation: Optional[str]
    preferredLanguage: Optional[str]
    surname: Optional[str]
    userPrincipalName: str
    id: str


class UserResponseSchema(UserSchema, ODataContextSchema):
    pass


class UsersSchema(BaseModel):
    odata_context: str = Field(None, alias="@odata.context")
    value: Optional[List[UserSchema]]


class MessageBodySchema(BaseModel):
    contentType: str
    content: str


class EmailAddressSchema(BaseModel):
    name: str
    address: str


class EmailAddressWrapperSchema(BaseModel):
    emailAddress: EmailAddressSchema


class MessageFlagSchema(BaseModel):
    flagStatus: str


class MessageSchema(BaseModel):
    odata_etag: Optional[str] = Field(None, alias="@odata.etag")
    id: str
    createdDateTime: str
    lastModifiedDateTime: str
    changeKey: str
    categories: List
    receivedDateTime: str
    sentDateTime: str
    hasAttachments: bool
    internetMessageId: str
    subject: str
    bodyPreview: str
    importance: str
    parentFolderId: str
    conversationId: str
    conversationIndex: str
    isDeliveryReceiptRequested: Optional[str]
    isReadReceiptRequested: bool
    isRead: bool
    isDraft: bool
    webLink: str
    inferenceClassification: str
    body: Optional[MessageBodySchema]
    sender: EmailAddressWrapperSchema
    from_email: EmailAddressWrapperSchema = Field(None, alias="from")
    toRecipients: List[EmailAddressWrapperSchema]
    ccRecipients: List[EmailAddressWrapperSchema]
    bccRecipients: List[EmailAddressWrapperSchema]
    replyTo: List[EmailAddressWrapperSchema]
    flag: MessageFlagSchema


class MessageResponseSchema(MessageSchema, ODataContextSchema):
    pass


class MessagesSchema(BaseModel):
    odata_context: Optional[str] = Field(None, alias="@odata.context")
    value: Optional[List[MessageSchema]]
    odata_nextLink: Optional[str] = Field(None, alias="@odata.nextLink")


class AttachmentSchema(BaseModel):
    odata_type: Optional[str] = Field(None, alias="@odata.type")
    odata_mediaContentType: Optional[str] = Field(None, alias="@odata.mediaContentType")
    id: str
    lastModifiedDateTime: str
    name: str
    contentType: str
    size: int
    isInline: bool
    contentId: Optional[Any]
    contentLocation: Optional[Any]
    contentBytes: str


class AttachmentsSchema(ODataNextLinkSchema, ODataContextSchema):
    value: Optional[List[AttachmentSchema]]
