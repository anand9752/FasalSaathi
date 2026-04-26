from fastapi import APIRouter

from app.api.routes import auth, crops, dashboard, farms, market, users, weather


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(farms.router, prefix="/farms", tags=["farms"])
api_router.include_router(crops.router, prefix="/crops", tags=["crops"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

