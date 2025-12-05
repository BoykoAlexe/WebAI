from pydantic import BaseModel


class MessageCreate(BaseModel):
    username: str
    text: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    name: str
    password: str


class ChatCreate(BaseModel):
    user_id: str
    title: str | None = None