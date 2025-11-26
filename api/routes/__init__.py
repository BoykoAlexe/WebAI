from fastapi import APIRouter
from .chat import router as chat_router

root_router = APIRouter()

root_router.include_router(chat_router)
