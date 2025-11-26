from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
from ..models.message import MessageCreate
from storage import messages
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

router = APIRouter()

MODEL_NAME = "qwen3:8b"
AI_NAME = MODEL_NAME.split(':')[0].title()


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


@router.get("/api/messages")
async def get_messages():
    return messages


@router.post("/api/messages")
async def send_message(msg: MessageCreate):
    user_msg = msg.model_dump()
    messages.append(user_msg)
    try:
        ai_text = get_ai_response(msg.text)
    except Exception as e:
        ai_text = f"[Ошибка генерации: {str(e)}]"
    ai_msg = {"username": AI_NAME, "text": ai_text}
    messages.append(ai_msg)
    return {
        "status": "ok",
        "user_message": user_msg,
        "ai_message": ai_msg
    }