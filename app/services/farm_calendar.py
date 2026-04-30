from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.crop import FarmCropCycle
from app.models.farm import Farm, SoilTest
from app.schemas.calendar import (
    FarmCalendarCropContext,
    FarmCalendarHealthMetric,
    FarmCalendarRecommendation,
    FarmCalendarResponse,
    FarmCalendarTask,
    FarmCalendarTimelineItem,
    FarmCalendarWeatherAlert,
    FarmCalendarWeatherSnapshot,
)
from app.services.weather import get_current_weather, get_forecast

Priority = Literal["critical", "high", "medium", "info", "optimal"]
HealthStatus = Literal["good", "warning", "critical", "info"]


@dataclass(frozen=True)
class StageDefinition:
    name: str
    name_hindi: str
    start_percent: int
    end_percent: int


STAGE_DEFINITIONS: list[StageDefinition] = [
    StageDefinition("Sowing", "बुवाई", 0, 5),
    StageDefinition("Germination", "अंकुरण", 5, 15),
    StageDefinition("Vegetative", "वानस्पतिक वृद्धि", 15, 65),
    StageDefinition("Flowering", "फूल आना", 65, 90),
    StageDefinition("Harvest", "कटाई", 90, 100),
]


def build_farm_calendar(
    db: Session,
    user_id: int,
    farm_id: int | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> FarmCalendarResponse:
    farm = _get_owned_farm_for_calendar(db, user_id, farm_id)
    active_cycle = _get_active_cycle(farm)
    latest_soil_test = max(farm.soil_tests, key=lambda item: item.test_date, default=None)

    weather = get_current_weather(db, location=farm.location, lat=lat, lon=lon)
    forecast = get_forecast(db, location=farm.location, lat=lat, lon=lon, days=3)
    forecast_rainfall = round(sum(item.rainfall for item in forecast.forecast), 1)

    crop_context = _build_crop_context(active_cycle)
    weather_snapshot = FarmCalendarWeatherSnapshot(
        location=weather.location,
        rainfall=weather.rainfall,
        forecast_rainfall=forecast_rainfall,
        temperature=weather.main.temp,
        humidity=weather.main.humidity,
        wind_speed=weather.wind.speed,
        summary=weather.weather[0].description if weather.weather else "Unavailable",
        source=weather.source,
        is_stale=weather.is_stale,
    )

    farm_health = _build_health_metrics(latest_soil_test, weather_snapshot)
    growth_timeline = _build_growth_timeline(crop_context)
    weather_alerts = _build_weather_alerts(weather_snapshot)
    tasks = _build_tasks(crop_context, latest_soil_test, weather_snapshot)
    recommendations = _build_recommendations(crop_context, latest_soil_test, weather_snapshot, tasks)

    return FarmCalendarResponse(
        farm_id=farm.id,
        generated_at=datetime.now(timezone.utc),
        crop_context=crop_context,
        weather=weather_snapshot,
        farm_health=farm_health,
        growth_timeline=growth_timeline,
        recommendations=recommendations,
        weather_alerts=weather_alerts,
        tasks=tasks,
    )


def _get_owned_farm_for_calendar(db: Session, user_id: int, farm_id: int | None) -> Farm:
    stmt = (
        select(Farm)
        .options(joinedload(Farm.soil_tests), joinedload(Farm.crop_cycles).joinedload(FarmCropCycle.crop))
        .where(Farm.owner_id == user_id)
        .order_by(Farm.created_at.asc())
    )
    if farm_id is not None:
        stmt = stmt.where(Farm.id == farm_id)

    farm = db.execute(stmt).unique().scalars().first()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


def _get_active_cycle(farm: Farm) -> FarmCropCycle | None:
    active_cycles = [cycle for cycle in farm.crop_cycles if cycle.status == "active" and cycle.crop]
    if active_cycles:
        return max(active_cycles, key=lambda cycle: cycle.created_at)

    completed_cycles = [cycle for cycle in farm.crop_cycles if cycle.crop]
    if completed_cycles:
        return max(completed_cycles, key=lambda cycle: cycle.created_at)

    return None


def _build_crop_context(cycle: FarmCropCycle | None) -> FarmCalendarCropContext | None:
    if not cycle or not cycle.crop:
        return None

    sowing_date = cycle.sowing_date or date.today()
    expected_harvest_date = cycle.expected_harvest_date or (sowing_date + timedelta(days=cycle.crop.duration))
    total_duration_days = max(cycle.crop.duration, 1)
    days_since_sowing = max((date.today() - sowing_date).days, 0)
    progress_percent = min(100, max(0, round((days_since_sowing / total_duration_days) * 100)))
    current_stage = _get_stage_definition(progress_percent)

    stage_span = max(current_stage.end_percent - current_stage.start_percent, 1)
    stage_progress_percent = min(
        100,
        max(0, round(((progress_percent - current_stage.start_percent) / stage_span) * 100)),
    )

    return FarmCalendarCropContext(
        crop_id=cycle.crop_id,
        crop_name=cycle.crop.name,
        crop_name_hindi=cycle.crop.name_hindi,
        season=cycle.season,
        sowing_date=sowing_date,
        expected_harvest_date=expected_harvest_date,
        days_since_sowing=days_since_sowing,
        total_duration_days=total_duration_days,
        current_stage=current_stage.name,
        current_stage_hindi=current_stage.name_hindi,
        stage_progress_percent=stage_progress_percent,
    )


def _get_stage_definition(progress_percent: int) -> StageDefinition:
    for stage in STAGE_DEFINITIONS:
        if progress_percent < stage.end_percent:
            return stage
    return STAGE_DEFINITIONS[-1]


def _build_growth_timeline(crop_context: FarmCalendarCropContext | None) -> list[FarmCalendarTimelineItem]:
    if not crop_context:
        return []

    total_duration = max(crop_context.total_duration_days, 1)
    progress_percent = min(100, max(0, round((crop_context.days_since_sowing / total_duration) * 100)))
    items: list[FarmCalendarTimelineItem] = []
    for stage in STAGE_DEFINITIONS:
        start_day = round((stage.start_percent / 100) * total_duration)
        end_day = max(start_day, round((stage.end_percent / 100) * total_duration))
        items.append(
            FarmCalendarTimelineItem(
                name=stage.name,
                name_hindi=stage.name_hindi,
                start_day=start_day,
                end_day=end_day,
                is_current=stage.name == _get_stage_definition(progress_percent).name,
            )
        )
    return items


def _build_health_metrics(
    soil_test: SoilTest | None,
    weather: FarmCalendarWeatherSnapshot,
) -> list[FarmCalendarHealthMetric]:
    if not soil_test:
        return [
            FarmCalendarHealthMetric(
                key="weather_temp",
                label="Temperature",
                value=weather.temperature,
                unit="C",
                status="info",
                note="Live weather is available, but add a soil test to unlock soil health scoring.",
            ),
            FarmCalendarHealthMetric(
                key="forecast_rain",
                label="Forecast Rainfall",
                value=weather.forecast_rainfall,
                unit="mm",
                status="info",
                note="Next 3-day rainfall estimate from OpenWeather.",
            ),
        ]

    return [
        FarmCalendarHealthMetric(
            key="soil_moisture",
            label="Soil Moisture",
            value=soil_test.soil_moisture,
            unit="%",
            status=_soil_moisture_status(soil_test.soil_moisture),
            note=_soil_moisture_note(soil_test.soil_moisture),
        ),
        FarmCalendarHealthMetric(
            key="soil_ph",
            label="pH",
            value=soil_test.soil_ph,
            unit="",
            status=_ph_status(soil_test.soil_ph),
            note=_ph_note(soil_test.soil_ph),
        ),
        FarmCalendarHealthMetric(
            key="nitrogen",
            label="Nitrogen",
            value=soil_test.nitrogen,
            unit="kg/ha",
            status=_nutrient_status(soil_test.nitrogen, warning=50, critical=35),
            note=_nutrient_note("Nitrogen", soil_test.nitrogen, warning=50, critical=35),
        ),
        FarmCalendarHealthMetric(
            key="temperature",
            label="Temperature",
            value=weather.temperature,
            unit="C",
            status="warning" if weather.temperature >= 35 else "good",
            note="Heat stress is rising." if weather.temperature >= 35 else "Air temperature is in a workable range.",
        ),
        FarmCalendarHealthMetric(
            key="forecast_rain",
            label="Forecast Rainfall",
            value=weather.forecast_rainfall,
            unit="mm",
            status="warning" if weather.forecast_rainfall >= 10 else "good",
            note="Heavy rain likely. Hold irrigation and field spraying." if weather.forecast_rainfall >= 10 else "No major rain disruption expected.",
        ),
    ]


def _soil_moisture_status(value: float) -> HealthStatus:
    if value < 20:
        return "critical"
    if value < 35:
        return "warning"
    return "good"


def _soil_moisture_note(value: float) -> str:
    if value < 20:
        return "Moisture is very low and irrigation is urgent."
    if value < 35:
        return "Moisture is dropping. Plan irrigation soon."
    return "Moisture is in a safe range."


def _ph_status(value: float) -> HealthStatus:
    if value < 5.5 or value > 8:
        return "critical"
    if value < 6 or value > 7.5:
        return "warning"
    return "good"


def _ph_note(value: float) -> str:
    if value < 5.5 or value > 8:
        return "pH is outside the safe crop range."
    if value < 6 or value > 7.5:
        return "pH is slightly off balance. Monitor soil amendments."
    return "pH is well balanced."


def _nutrient_status(value: float, warning: float, critical: float) -> HealthStatus:
    if value < critical:
        return "critical"
    if value < warning:
        return "warning"
    return "good"


def _nutrient_note(label: str, value: float, warning: float, critical: float) -> str:
    if value < critical:
        return f"{label} is deficient."
    if value < warning:
        return f"{label} is slightly low."
    return f"{label} is in a healthy range."


def _build_weather_alerts(weather: FarmCalendarWeatherSnapshot) -> list[FarmCalendarWeatherAlert]:
    alerts: list[FarmCalendarWeatherAlert] = []
    if weather.forecast_rainfall >= 10:
        alerts.append(
            FarmCalendarWeatherAlert(
                title="Rain expected",
                message=f"About {weather.forecast_rainfall} mm rain is expected in the next 3 days. Skip irrigation and protect fertilizer application.",
                priority="high",
            )
        )
    if weather.temperature >= 35:
        alerts.append(
            FarmCalendarWeatherAlert(
                title="Heatwave risk",
                message=f"Temperature is {weather.temperature:.0f}C. Increase water monitoring and prefer evening irrigation.",
                priority="critical",
            )
        )
    if weather.wind_speed >= 8:
        alerts.append(
            FarmCalendarWeatherAlert(
                title="Wind advisory",
                message=f"Wind speed is {weather.wind_speed:.1f} m/s. Avoid spraying until conditions calm down.",
                priority="medium",
            )
        )
    if not alerts:
        alerts.append(
            FarmCalendarWeatherAlert(
                title="Weather stable",
                message="No severe weather interruption is expected right now.",
                priority="info",
            )
        )
    return alerts


def _build_tasks(
    crop_context: FarmCalendarCropContext | None,
    soil_test: SoilTest | None,
    weather: FarmCalendarWeatherSnapshot,
) -> list[FarmCalendarTask]:
    if not crop_context:
        return [
            FarmCalendarTask(
                id="setup-soil-test",
                date=date.today(),
                task="Add a crop and soil test",
                task_hindi="फसल और मिट्टी परीक्षण जोड़ें",
                category="general",
                priority="info",
                reason="The calendar becomes smart only after an active crop and recent soil test are linked to the farm.",
                recommendation="Connect a crop cycle and save the latest soil values to unlock irrigation, fertilizer, and weather-aware planning.",
            )
        ]

    tasks: list[FarmCalendarTask] = []
    task_ids: set[str] = set()
    crop_name = crop_context.crop_name
    days_since_sowing = crop_context.days_since_sowing
    irrigation_interval = _irrigation_interval_days(crop_name)

    def add_task(task: FarmCalendarTask) -> None:
        if task.id in task_ids:
            return
        task_ids.add(task.id)
        tasks.append(task)

    add_task(
        FarmCalendarTask(
            id="milestone-sowing",
            date=crop_context.sowing_date,
            task=f"Sowing completed for {crop_name}",
            task_hindi=f"{crop_context.crop_name_hindi} की बुवाई",
            category="milestone",
            priority="info",
            reason=f"{crop_name} crop cycle started on {crop_context.sowing_date.isoformat()}.",
            recommendation="Use this as the reference point for all future irrigation, fertilizer, and harvest tasks.",
        )
    )

    for irrigation_day in range(irrigation_interval, crop_context.total_duration_days + 1, irrigation_interval):
        irrigation_date = crop_context.sowing_date + timedelta(days=irrigation_day)
        priority: Priority = "optimal"
        reason_bits = [
            f"{crop_name} typically needs irrigation every {irrigation_interval} days",
            f"current stage is {crop_context.current_stage}",
        ]
        recommendation = "Monitor field moisture before irrigation and prefer early morning or evening application."

        if soil_test and soil_test.soil_moisture < 20 and weather.temperature > 30 and abs(irrigation_day - days_since_sowing) <= 2:
            priority = "critical"
            reason_bits = [
                f"Soil moisture is low at {soil_test.soil_moisture:.0f}%",
                f"temperature is high at {weather.temperature:.0f}C",
                f"{crop_name} requires regular watering around every {irrigation_interval} days",
            ]
            recommendation = "Irrigate immediately with a focused watering cycle and recheck moisture within 24 hours."
        elif soil_test and soil_test.soil_moisture < 35 and abs(irrigation_day - days_since_sowing) <= 3:
            priority = "high"
            reason_bits = [
                f"Soil moisture is dropping to {soil_test.soil_moisture:.0f}%",
                f"{crop_name} is in the {crop_context.current_stage.lower()} stage",
                f"this is the next planned irrigation window",
            ]
            recommendation = "Plan irrigation within 1 to 2 days to avoid stress."

        if weather.forecast_rainfall >= 10 and abs(irrigation_day - days_since_sowing) <= 2:
            priority = "info"
            reason_bits = [
                f"Rainfall of about {weather.forecast_rainfall:.1f} mm is expected soon",
                f"scheduled irrigation window is day {irrigation_day}",
                "natural rainfall can cover part of the crop water need",
            ]
            recommendation = "Skip or reduce irrigation until rainfall passes and then reassess soil moisture."

        add_task(
            FarmCalendarTask(
                id=f"irrigation-{irrigation_day}",
                date=irrigation_date,
                task="Irrigation",
                task_hindi="सिंचाई",
                category="irrigation",
                priority=priority,
                reason="; ".join(reason_bits),
                recommendation=recommendation,
                suggested_time="6:00 AM" if weather.temperature < 32 else "6:30 PM",
            )
        )

    fertilizer_days = [20, 45, 75]
    for offset in fertilizer_days:
        if offset > crop_context.total_duration_days:
            continue
        fertilizer_date = crop_context.sowing_date + timedelta(days=offset)
        nitrogen_value = soil_test.nitrogen if soil_test else None
        priority: Priority = "medium"
        if nitrogen_value is not None and nitrogen_value < 35 and abs(offset - days_since_sowing) <= 5:
            priority = "high"
        recommendation = "Apply nitrogen fertilizer on moist soil and avoid heavy rain just after application."
        if weather.forecast_rainfall >= 10 and abs(offset - days_since_sowing) <= 3:
            recommendation = "Delay fertilizer until heavy rain risk reduces to avoid nutrient loss."
            priority = "info"

        add_task(
            FarmCalendarTask(
                id=f"fertilizer-{offset}",
                date=fertilizer_date,
                task="Apply Nitrogen Fertilizer",
                task_hindi="नाइट्रोजन उर्वरक डालें",
                category="fertilizer",
                priority=priority,
                reason=_fertilizer_reason(crop_name, offset, nitrogen_value, weather.forecast_rainfall),
                recommendation=recommendation,
                suggested_time="7:00 AM",
            )
        )

    if soil_test and soil_test.soil_moisture < 20 and weather.temperature > 30:
        add_task(
            FarmCalendarTask(
                id="urgent-irrigation-now",
                date=date.today(),
                task="Irrigation Needed",
                task_hindi="तुरंत सिंचाई करें",
                category="irrigation",
                priority="critical",
                reason=f"Soil moisture low ({soil_test.soil_moisture:.0f}%); temperature high ({weather.temperature:.0f}C); {crop_name} is in the {crop_context.current_stage.lower()} stage.",
                recommendation="Start irrigation now and inspect water coverage across the active plot.",
                suggested_time="Immediately",
            )
        )

    pest_risk = _pest_risk(soil_test, weather, crop_context.current_stage)
    if pest_risk:
        add_task(
            FarmCalendarTask(
                id="pest-risk-check",
                date=date.today() + timedelta(days=1),
                task="Pest Risk Inspection",
                task_hindi="कीट जोखिम जांच",
                category="pest",
                priority=pest_risk[0],
                reason=pest_risk[1],
                recommendation="Inspect leaf undersides, check sticky traps, and spray only if threshold is confirmed.",
                suggested_time="7:30 AM",
            )
        )

    if weather.wind_speed >= 8:
        add_task(
            FarmCalendarTask(
                id="wind-spray-alert",
                date=date.today(),
                task="Avoid spraying today",
                task_hindi="आज छिड़काव न करें",
                category="weather",
                priority="medium",
                reason=f"Wind speed is {weather.wind_speed:.1f} m/s, which can cause uneven spray coverage and drift.",
                recommendation="Wait for calmer wind before pesticide or foliar spray applications.",
            )
        )

    add_task(
        FarmCalendarTask(
            id="milestone-harvest",
            date=crop_context.expected_harvest_date,
            task="Harvest window",
            task_hindi="कटाई का समय",
            category="milestone",
            priority="info",
            reason=f"{crop_name} is expected to complete its cycle around day {crop_context.total_duration_days}.",
            recommendation="Prepare labor, transport, and storage 5 to 7 days before harvest.",
        )
    )

    return sorted(tasks, key=lambda item: (item.date, _priority_sort_index(item.priority)))


def _fertilizer_reason(
    crop_name: str,
    offset: int,
    nitrogen_value: float | None,
    forecast_rainfall: float,
) -> str:
    parts = [f"{crop_name} follows a planned fertilizer window around day {offset}"]
    if nitrogen_value is not None:
        if nitrogen_value < 35:
            parts.append(f"soil nitrogen is deficient at {nitrogen_value:.0f} kg/ha")
        elif nitrogen_value < 50:
            parts.append(f"soil nitrogen is moderate at {nitrogen_value:.0f} kg/ha")
        else:
            parts.append(f"soil nitrogen is currently {nitrogen_value:.0f} kg/ha")
    if forecast_rainfall >= 10:
        parts.append(f"rainfall forecast is {forecast_rainfall:.1f} mm")
    return "; ".join(parts)


def _irrigation_interval_days(crop_name: str) -> int:
    normalized = crop_name.strip().lower()
    if normalized in {"wheat", "soybean", "maize"}:
        return 7
    if normalized in {"chickpea", "mustard"}:
        return 10
    return 8


def _pest_risk(
    soil_test: SoilTest | None,
    weather: FarmCalendarWeatherSnapshot,
    current_stage: str,
) -> tuple[Literal["medium", "high"], str] | None:
    humidity = weather.humidity
    temperature = weather.temperature
    moisture = soil_test.soil_moisture if soil_test else None

    if humidity >= 75 and 24 <= temperature <= 33:
        return (
            "high",
            f"Humidity is high at {humidity:.0f}%, temperature is {temperature:.0f}C, and the crop is in the {current_stage.lower()} stage.",
        )
    if moisture is not None and moisture >= 70 and humidity >= 65:
        return (
            "medium",
            f"Soil moisture is high at {moisture:.0f}% and humidity is {humidity:.0f}%, which can increase pest and disease pressure.",
        )
    return None


def _build_recommendations(
    crop_context: FarmCalendarCropContext | None,
    soil_test: SoilTest | None,
    weather: FarmCalendarWeatherSnapshot,
    tasks: list[FarmCalendarTask],
) -> list[FarmCalendarRecommendation]:
    recommendations: list[FarmCalendarRecommendation] = []

    if not crop_context:
        return [
            FarmCalendarRecommendation(
                title="Add crop context",
                message="Select the active crop and set a sowing date to unlock stage-based calendar planning.",
                priority="info",
            )
        ]

    if soil_test and soil_test.soil_moisture < 20:
        recommendations.append(
            FarmCalendarRecommendation(
                title="Irrigate within 24 hours",
                message=f"Soil moisture is {soil_test.soil_moisture:.0f}% during the {crop_context.current_stage.lower()} stage.",
                priority="critical",
            )
        )
    elif soil_test and soil_test.soil_moisture < 35:
        recommendations.append(
            FarmCalendarRecommendation(
                title="Irrigate within 2 days",
                message=f"Moisture is falling to {soil_test.soil_moisture:.0f}%, so plan the next watering cycle soon.",
                priority="high",
            )
        )

    if soil_test and soil_test.nitrogen < 35:
        recommendations.append(
            FarmCalendarRecommendation(
                title="Apply urea now",
                message=f"Nitrogen is deficient at {soil_test.nitrogen:.0f} kg/ha and the crop is at day {crop_context.days_since_sowing}.",
                priority="high",
            )
        )

    if weather.forecast_rainfall >= 10:
        recommendations.append(
            FarmCalendarRecommendation(
                title="Rain expected, hold irrigation",
                message=f"About {weather.forecast_rainfall:.1f} mm rain is expected soon, so postpone watering unless moisture becomes critical.",
                priority="medium",
            )
        )

    if weather.wind_speed >= 8:
        recommendations.append(
            FarmCalendarRecommendation(
                title="Avoid spraying",
                message=f"Wind speed is {weather.wind_speed:.1f} m/s, so keep pesticide spraying on hold.",
                priority="medium",
            )
        )

    if not recommendations:
        next_task = next((task for task in tasks if task.date >= date.today()), None)
        recommendations.append(
            FarmCalendarRecommendation(
                title="Farm conditions look stable",
                message=(
                    f"Current stage is {crop_context.current_stage}. "
                    f"Next planned task: {next_task.task} on {next_task.date.isoformat()}."
                    if next_task
                    else f"Current stage is {crop_context.current_stage}. Continue routine monitoring."
                ),
                priority="info",
            )
        )

    return recommendations[:4]


def _priority_sort_index(priority: Priority) -> int:
    order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "info": 3,
        "optimal": 4,
    }
    return order[priority]
