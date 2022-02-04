import enum


class Endpoint(str, enum.Enum):
    users = "https://graph.microsoft.com/v1.0/users"
