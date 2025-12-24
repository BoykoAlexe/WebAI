from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    PROJECT_NAME: str = "Chat API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_ROOT_PATH: str = ""
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 1
    OLLAMA_MODEL: str = "gemma3:1b"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_app_settings() -> AppSettings:
    return AppSettings()
