import json
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, List


DATA_FILE = Path("storage_data.json")

_default_data = {
    "users": [],
    "logins": [],
    "chats": [],
    "messages": [],
}


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _load_data() -> Dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # В случае повреждения файла начинаем с чистого состояния
            return deepcopy(_default_data)
    return deepcopy(_default_data)


def _save_data(data: Dict) -> None:
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


_data = _load_data()


def get_or_create_user(username: str) -> Dict:
    """Находит пользователя по имени или создаёт нового."""
    existing = next((u for u in _data["users"] if u["username"].lower() == username.lower()), None)
    if existing:
        _data["logins"].append({"user_id": existing["id"], "timestamp": _now_iso()})
        _save_data(_data)
        return existing

    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "created_at": _now_iso(),
    }
    _data["users"].append(user)
    _data["logins"].append({"user_id": user["id"], "timestamp": _now_iso()})
    _save_data(_data)
    return user


def get_login_history(user_id: str) -> List[Dict]:
    return [entry for entry in _data["logins"] if entry["user_id"] == user_id]


def create_chat(user_id: str, title: str) -> Dict:
    chat = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title or "Новый чат",
        "created_at": _now_iso(),
    }
    _data["chats"].append(chat)
    _save_data(_data)
    return chat


def get_chats(user_id: str) -> List[Dict]:
    return [chat for chat in _data["chats"] if chat["user_id"] == user_id]


def get_chat(chat_id: str) -> Dict | None:
    return next((chat for chat in _data["chats"] if chat["id"] == chat_id), None)


def add_message(chat_id: str, username: str, text: str, role: str) -> Dict:
    message = {
        "id": str(uuid.uuid4()),
        "chat_id": chat_id,
        "username": username,
        "text": text,
        "role": role,
        "created_at": _now_iso(),
    }
    _data["messages"].append(message)
    _save_data(_data)
    return message


def get_messages(chat_id: str) -> List[Dict]:
    return [msg for msg in _data["messages"] if msg["chat_id"] == chat_id]