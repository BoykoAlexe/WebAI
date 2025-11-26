from functools import partial
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware as cors
from config import get_app_settings
from api.routes.chat import router

# Кастомизация Swagger UI (если у вас локальные файлы)
get_swagger_ui_html = partial(
    get_swagger_ui_html,
    swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
    swagger_css_url="/static/swagger-ui/swagger-ui.css",
)


def get_application() -> FastAPI:
    config = get_app_settings()

    application: FastAPI = FastAPI(**dict(
        title=config.PROJECT_NAME,
        description=f"API сервис {config.PROJECT_NAME}",
        root_path=config.API_ROOT_PATH,
        version=config.VERSION,
        debug=config.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
    ))

    # Подключение статики
    application.mount("/static", StaticFiles(directory=Path("static")), name="static")

    # CORS
    application.add_middleware(
        cors,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Роуты
    application.include_router(router)

    return application


app = get_application()
