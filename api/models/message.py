from pydantic import BaseModel


class MessageCreate(BaseModel):
    username: str
    text: str


class LoginRequest(BaseModel):
    username: str


class ChatCreate(BaseModel):
    user_id: str
    title: str | None = None