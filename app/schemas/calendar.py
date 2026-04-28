from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class FarmCalendarCropContext(BaseModel):
    crop_id: int
    crop_name: str
    crop_name_hindi: str
    season: str
    sowing_date: date
    expected_harvest_date: date
    days_since_sowing: int
    total_duration_days: int
    current_stage: str
    current_stage_hindi: str
    stage_progress_percent: int


class FarmCalendarHealthMetric(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    status: Literal["good", "warning", "critical", "info"]
    note: str


class FarmCalendarTimelineItem(BaseModel):
    name: str
    name_hindi: str
    start_day: int
    end_day: int
    is_current: bool = False


class FarmCalendarRecommendation(BaseModel):
    title: str
    message: str
    priority: Literal["critical", "high", "medium", "info"]


class FarmCalendarTask(BaseModel):
    id: str
    date: date
    task: str
    task_hindi: str
    category: Literal["irrigation", "fertilizer", "pest", "weather", "milestone", "general"]
    priority: Literal["critical", "high", "medium", "info", "optimal"]
    reason: str
    recommendation: str
    suggested_time: str | None = None


class FarmCalendarWeatherAlert(BaseModel):
    title: str
    message: str
    priority: Literal["critical", "high", "medium", "info"]


class FarmCalendarWeatherSnapshot(BaseModel):
    location: str
    rainfall: float
    forecast_rainfall: float
    temperature: float
    humidity: float
    wind_speed: float
    summary: str
    source: Literal["live", "cache", "fallback"]
    is_stale: bool


class FarmCalendarResponse(BaseModel):
    farm_id: int
    generated_at: datetime
    crop_context: FarmCalendarCropContext | None = None
    weather: FarmCalendarWeatherSnapshot
    farm_health: list[FarmCalendarHealthMetric]
    growth_timeline: list[FarmCalendarTimelineItem]
    recommendations: list[FarmCalendarRecommendation]
    weather_alerts: list[FarmCalendarWeatherAlert]
    tasks: list[FarmCalendarTask]
