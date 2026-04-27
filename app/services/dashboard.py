from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.crop import Crop, FarmCropCycle
from app.models.farm import Farm
from app.schemas.crop import CropRecommendationRequest
from app.schemas.dashboard import DashboardOverview, FarmVitals, TodayPriority, YieldForecast
from app.schemas.farm import CropCycleRead, FarmRead, SoilTestRead
from app.services.market import get_current_prices
from app.services.recommendation import build_recommendations
from app.services.weather import get_current_weather


def _serialize_crop_cycle(cycle: FarmCropCycle) -> CropCycleRead:
    return CropCycleRead(
        id=cycle.id,
        crop_id=cycle.crop_id,
        crop_name=cycle.crop.name,
        crop_name_hindi=cycle.crop.name_hindi,
        season=cycle.season,
        year=cycle.year,
        sowing_date=cycle.sowing_date,
        expected_harvest_date=cycle.expected_harvest_date,
        area=cycle.area,
        status=cycle.status,
        yield_achieved=cycle.yield_achieved,
        profit_loss=cycle.profit_loss,
    )


def build_dashboard_overview(db: Session, user_id: int) -> DashboardOverview:
    farm = db.execute(
        select(Farm)
        .options(joinedload(Farm.soil_tests), joinedload(Farm.crop_cycles).joinedload(FarmCropCycle.crop))
        .where(Farm.owner_id == user_id)
        .order_by(Farm.created_at.asc())
    ).unique().scalar_one_or_none()
    weather = get_current_weather(db, location=farm.location if farm else None)
    market_alert = get_current_prices(db)[0] if get_current_prices(db) else None

    if not farm:
        return DashboardOverview(weather=weather, market_alert=market_alert, recommendation_preview=[])

    active_cycle = next((cycle for cycle in farm.crop_cycles if cycle.status == "active"), None)
    latest_soil_test = max(farm.soil_tests, key=lambda item: item.test_date, default=None)

    recommendations = build_recommendations(
        list(db.scalars(select(Crop).order_by(Crop.name.asc()))),
        CropRecommendationRequest(
            soil_type=farm.soil_type,
            season=active_cycle.season if active_cycle else "Kharif",
            location=farm.location,
            irrigation_type=farm.irrigation_type,
        ),
    )[:3]

    overview = DashboardOverview(
        farm=FarmRead(
            id=farm.id,
            name=farm.name,
            location=farm.location,
            area=farm.area,
            soil_type=farm.soil_type,
            irrigation_type=farm.irrigation_type,
            owner_id=farm.owner_id,
            created_at=farm.created_at,
            updated_at=farm.updated_at,
            soil_tests=[SoilTestRead.model_validate(item) for item in sorted(farm.soil_tests, key=lambda x: x.test_date, reverse=True)],
            crop_cycles=[_serialize_crop_cycle(item) for item in sorted(farm.crop_cycles, key=lambda x: (x.year, x.created_at), reverse=True)],
        ),
        active_crop=_serialize_crop_cycle(active_cycle) if active_cycle else None,
        latest_soil_test=SoilTestRead.model_validate(latest_soil_test) if latest_soil_test else None,
        weather=weather,
        market_alert=market_alert,
        recommendation_preview=recommendations,
    )
    if active_cycle and active_cycle.crop:
        crop = active_cycle.crop
        overview.today_priority = TodayPriority(
            title=f"Check {crop.name} crop condition",
            description="Monitor moisture and pest pressure in the active field before evening.",
            recommended_time="6:00 PM",
            priority="high",
        )
        if latest_soil_test:
            overview.farm_vitals = FarmVitals(
                soil_moisture=65.0,
                soil_ph=latest_soil_test.ph,
                nitrogen=latest_soil_test.nitrogen,
                phosphorus=latest_soil_test.phosphorus,
                potassium=latest_soil_test.potassium,
            )
        overview.yield_forecast = YieldForecast(
            crop_name=crop.name_hindi,
            range_label=f"{crop.estimated_yield_min:.0f}-{crop.estimated_yield_max:.0f} quintal/acre",
            progress_percent=75,
            expected_harvest=active_cycle.expected_harvest_date.isoformat() if active_cycle.expected_harvest_date else "",
            estimated_income_range=(
                f"Rs. {int(crop.estimated_profit * 0.9):,} - Rs. {int(crop.estimated_profit * 1.1):,}"
            ),
        )
    return overview
