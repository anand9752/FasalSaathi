from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.session import init_db
from app.services.seed import seed_database


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.on_event("startup")
    def startup_event() -> None:
        init_db()
        seed_database()

    @application.get("/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_application()

