from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pathlib import Path

from ..models.message import ChatCreate, LoginRequest, MessageCreate
from storage import (
    add_message,
    create_chat,
    get_chat,
    get_chats,
    get_login_history,
    get_messages,
    get_or_create_user,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

router = APIRouter()

MODEL_NAME = "qwen3:8b"
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


@router.post("/api/login")
async def login(payload: LoginRequest):
    user = get_or_create_user(payload.username)
    history = get_login_history(user["id"])
    chats = get_chats(user["id"])
    return {"user": user, "login_history": history, "chats": chats}


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

    user_msg = add_message(chat_id, msg.username, msg.text, role="user")

    try:
        ai_text = get_ai_response(msg.text)
    except Exception as e:
        ai_text = f"[Ошибка генерации: {str(e)}]"

    ai_msg = add_message(chat_id, AI_NAME, ai_text, role="ai")

    return {
        "status": "ok",
        "user_message": user_msg,
        "ai_message": ai_msg,
    }