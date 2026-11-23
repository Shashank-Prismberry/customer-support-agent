from fastapi import FastAPI

from support_agent.api.routes import router
from support_agent.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
    )
    application.include_router(router)
    return application


app = create_app()
