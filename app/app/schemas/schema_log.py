from pydantic import BaseModel


class LogSchema(BaseModel):
    trace_id: str = None
    scope: str = None
