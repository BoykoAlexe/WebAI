from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pathlib import Path

from ..models.message import ChatCreate, LoginRequest, MessageCreate, RegisterRequest
from storage import (
    add_message,
    authenticate_user,
    create_chat,
    get_chat,
    get_chats,
    get_messages,
    register_user,
    update_last_user_message,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

router = APIRouter()

MODEL_NAME = "gemma3:1b"
AI_NAME = MODEL_NAME.split(":")[0].title()


def get_ai_response(question: str) -> str:
    """Получает ответ от Ollama."""
    template = """Answer the question below.

    Question: {question}

    Answer:"""
    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model=MODEL_NAME)
    chain = prompt | model
    return chain.invoke({"question": question}).strip()


@router.get("/", response_class=HTMLResponse)
async def get_chat_page():
    html_path = Path("static/index.html")
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Файл index.html не найден")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@router.post("/api/register")
async def register(payload: RegisterRequest):
    try:
        user = register_user(payload.username, payload.password, payload.name)
    except ValueError as exc:  # pragma: no cover - ValueError used for validation
        raise HTTPException(status_code=400, detail=str(exc))

    chats = get_chats(user["id"])
    return {"user": user, "chats": chats}


@router.post("/api/login")
async def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверные имя пользователя или пароль")

    chats = get_chats(user["id"])
    return {"user": user, "chats": chats}


@router.get("/api/chats")
async def list_chats(user_id: str = Query(..., description="Идентификатор пользователя")):
    return get_chats(user_id)


@router.post("/api/chats")
async def create_new_chat(payload: ChatCreate):
    return create_chat(payload.user_id, payload.title or "Новый чат")


@router.get("/api/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: str):
    chat = get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return get_messages(chat_id)


@router.post("/api/chats/{chat_id}/messages")
async def send_message(chat_id: str, msg: MessageCreate):
    chat = get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")

    user_msg, updated_chat = add_message(chat_id, msg.username, msg.text, role="user")

    try:
        ai_text = get_ai_response(msg.text)
    except Exception as e:
        ai_text = f"[Ошибка генерации: {str(e)}]"

    ai_msg, _ = add_message(chat_id, AI_NAME, ai_text, role="ai")

    return {
        "status": "ok",
        "user_message": user_msg,
        "ai_message": ai_msg,
        "chat": updated_chat or chat,
    }


@router.put("/api/chats/{chat_id}/messages/last")
async def edit_last_message(chat_id: str, msg: MessageCreate):
    chat = get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")

    user_msg, _ = update_last_user_message(chat_id, msg.username, msg.text)
    if not user_msg:
        raise HTTPException(status_code=404, detail="Нет сообщения для редактирования")

    try:
        ai_text = get_ai_response(msg.text)
    except Exception as e:  # pragma: no cover - внешний сервис
        ai_text = f"[Ошибка генерации: {str(e)}]"

    ai_msg, updated_chat = add_message(chat_id, AI_NAME, ai_text, role="ai")

    return {
        "status": "ok",
        "user_message": user_msg,
        "ai_message": ai_msg,
        "chat": updated_chat or chat,
    }