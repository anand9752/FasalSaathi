from fastapi import APIRouter

from app.api.routes import auth, calendar, crops, dashboard, farms, inventory, market, recommendations, soil_tests, users, weather


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(farms.router, prefix="/farms", tags=["farms"])
api_router.include_router(crops.router, prefix="/crops", tags=["crops"])
api_router.include_router(recommendations.router, tags=["recommendations"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(calendar.router, tags=["calendar"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(soil_tests.router, prefix="/soil-test", tags=["soil-test"])
