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
        allow_origins=settings.cors_origins if "*" not in settings.cors_origins else [],
        allow_origin_regex=".*" if "*" in settings.cors_origins else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.on_event("startup")
    def startup_event() -> None:
        init_db()
        seed_database()
        from app.services.weather_alert import start_scheduler as start_weather_scheduler
        from app.services.market_alert import start_market_scheduler
        from app.services.weather_alert import scheduler
        
        start_weather_scheduler()
        start_market_scheduler(scheduler)

    @application.get("/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_application()

