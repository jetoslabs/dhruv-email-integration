from typing import List, Optional, Any, Union

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
    name: Optional[str]
    address: Optional[str]


class EmailAddressWrapperSchema(BaseModel):
    emailAddress: EmailAddressSchema


class MessageFlagSchema(BaseModel):
    flagStatus: str


class MessageSchema(BaseModel):
    odata_type: Optional[str] = Field(None, alias="@odata.type")
    odata_etag: str = Field(None, alias="@odata.etag")
    id: str
    createdDateTime: str
    lastModifiedDateTime: str
    changeKey: str
    categories: List
    receivedDateTime: str
    sentDateTime: Optional[str]
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
    sender: Optional[EmailAddressWrapperSchema]  # Optional, isDraft= True
    from_email: Optional[EmailAddressWrapperSchema] = Field(None, alias="from")  # Optional, isDraft= True
    toRecipients: Optional[List[EmailAddressWrapperSchema]]
    ccRecipients: List[EmailAddressWrapperSchema]
    bccRecipients: List[EmailAddressWrapperSchema]
    replyTo: List[EmailAddressWrapperSchema]
    flag: MessageFlagSchema
    # Optional, odata_type = '#microsoft.graph.eventMessageResponse'
    meetingMessageType: Optional[str]
    type: Optional[str]
    isOutOfDate: Optional[bool]
    isAllDay: Optional[bool]
    isDelegated: Optional[bool]
    responseType: Optional[str]
    startDateTime: Optional[dict]
    endDateTime: Optional[dict]
    location: Optional[dict]
    recurrence: Optional[Any]


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
    contentBytes: Optional[str]


class AttachmentsSchema(ODataNextLinkSchema, ODataContextSchema):
    value: Optional[List[AttachmentSchema]]


class AttachmentInCreateMessage(BaseModel):
    odata_type: str = Field(None, alias="@odata.type")
    name: str
    contentType: str
    contentBytes: str

    # class Config:
    #     allow_population_by_field_name = True


class CreateMessageSchema(BaseModel):
    subject: Optional[str]
    body: Optional[MessageBodySchema]
    toRecipients: List[EmailAddressWrapperSchema]
    ccRecipients: Optional[List[EmailAddressWrapperSchema]]
    attachments: Union[Optional[List[AttachmentInCreateMessage]], Optional[List[dict]]]
    # attachments: Optional[List[dict]]


class SendMessageRequestSchema(BaseModel):
    message: CreateMessageSchema
    saveToSentItems: bool = True
