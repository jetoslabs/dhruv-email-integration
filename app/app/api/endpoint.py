import enum


class Endpoint(str, enum.Enum):
    users = "https://graph.microsoft.com/v1.0/users"
    send_mail = "https://graph.microsoft.com/v1.0/users/{id}/sendMail"
    message_delta = "https://graph.microsoft.com/v1.0/users/{id}/mailFolders/{id}/messages/delta"
    list_message = "https://graph.microsoft.com/v1.0/users/{id}/messages"
