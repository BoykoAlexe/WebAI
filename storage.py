import hashlib
import json
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _find_user(username: str) -> Optional[Dict]:
    return next((u for u in _data["users"] if u["username"].lower() == username.lower()), None)


def _public_user(user: Dict) -> Dict:
    return {k: v for k, v in user.items() if k != "password_hash"}


def get_or_create_user(username: str) -> Dict:
    """Находит пользователя по имени или создаёт нового."""
    existing = _find_user(username)
    if existing:
        _data["logins"].append({"user_id": existing["id"], "timestamp": _now_iso()})
        _save_data(_data)
        return _public_user(existing)

    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": _hash_password(""),
        "created_at": _now_iso(),
    }
    _data["users"].append(user)
    _data["logins"].append({"user_id": user["id"], "timestamp": _now_iso()})
    _save_data(_data)
    return _public_user(user)


def register_user(username: str, password: str, name: str) -> Dict:
    if not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")
    if not name.strip():
        raise ValueError("Имя не может быть пустым")
    if not password:
        raise ValueError("Пароль не может быть пустым")

    existing = _find_user(username)
    if existing and existing.get("password_hash"):
        raise ValueError("Пользователь с таким именем уже существует")

    # Разрешаем задать пароль для пользователя из старых данных без пароля
    if existing and not existing.get("password_hash"):
        existing["password_hash"] = _hash_password(password)
        existing["name"] = name
        _save_data(_data)
        return _public_user(existing)

    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "name": name,
        "password_hash": _hash_password(password),
        "created_at": _now_iso(),
    }
    _data["users"].append(user)
    _save_data(_data)
    return _public_user(user)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = _find_user(username)
    if not user or not user.get("password_hash"):
        return None

    if user["password_hash"] != _hash_password(password):
        return None

    _data["logins"].append({"user_id": user["id"], "timestamp": _now_iso()})
    _save_data(_data)
    return _public_user(user)


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


def update_last_user_message(
    chat_id: str, username: str, text: str
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """Обновляет последнее пользовательское сообщение в чате.

    Возвращает кортеж (обновлённое сообщение пользователя, удалённое AI-сообщение).
    Если подходящее сообщение не найдено, возвращает (None, None).
    """
    chat_message_indexes = [
        idx for idx, msg in enumerate(_data["messages"]) if msg["chat_id"] == chat_id
    ]
    if not chat_message_indexes:
        return None, None

    last_user_index = next(
        (
            idx
            for idx in reversed(chat_message_indexes)
            if _data["messages"][idx]["role"] == "user"
            and _data["messages"][idx]["username"] == username
        ),
        None,
    )

    if last_user_index is None:
        return None, None

    user_msg = _data["messages"][last_user_index]
    user_msg["text"] = text
    user_msg["updated_at"] = _now_iso()

    removed_ai = None
    last_index = chat_message_indexes[-1]
    last_msg = _data["messages"][last_index]
    if last_msg["role"] == "ai":
        removed_ai = _data["messages"].pop(last_index)

    _save_data(_data)
    return user_msg, removed_ai


def add_message(chat_id: str, username: str, text: str, role: str) -> Tuple[Dict, Optional[Dict]]:
    existing_messages = [msg for msg in _data["messages"] if msg["chat_id"] == chat_id]
    is_first_for_chat = not existing_messages and role == "user"
    message = {
        "id": str(uuid.uuid4()),
        "chat_id": chat_id,
        "username": username,
        "text": text,
        "role": role,
        "created_at": _now_iso(),
    }

    updated_chat = None
    if is_first_for_chat:
        chat = get_chat(chat_id)
        if chat:
            chat["title"] = (text.strip() or "Новый чат")[:60]
            updated_chat = chat

    _data["messages"].append(message)
    _save_data(_data)
    return message, updated_chat


def get_messages(chat_id: str) -> List[Dict]:
    return [msg for msg in _data["messages"] if msg["chat_id"] == chat_id]
