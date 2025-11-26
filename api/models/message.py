from pydantic import BaseModel


class MessageCreate(BaseModel):
    username: str
    text: str
