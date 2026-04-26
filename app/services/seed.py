from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.crop import Crop, FarmCropCycle
from app.models.farm import Farm, SoilTest
from app.models.market import MarketPrice
from app.models.user import User
from app.models.weather import WeatherData


def seed_database() -> None:
    with SessionLocal() as db:
        has_crops = db.scalar(select(Crop.id).limit(1))
        if has_crops:
            return

        crops = [
            Crop(
                name="Soybean",
                name_hindi="सोयाबीन",
                scientific_name="Glycine max",
                season="Kharif",
                duration=110,
                water_requirement=60,
                soil_compatibility="loamy, black, clay",
                estimated_yield_min=16,
                estimated_yield_max=18,
                estimated_profit=48000,
                investment_per_acre=28000,
                market_demand_level="high",
                risk_level="medium",
                description="Strong kharif crop for central India with stable mandi demand.",
            ),
            Crop(
                name="Wheat",
                name_hindi="गेहूं",
                scientific_name="Triticum aestivum",
                season="Rabi",
                duration=125,
                water_requirement=55,
                soil_compatibility="loamy, alluvial, black",
                estimated_yield_min=22,
                estimated_yield_max=24,
                estimated_profit=65000,
                investment_per_acre=25000,
                market_demand_level="high",
                risk_level="low",
                description="Reliable rabi crop with strong procurement and consistent market demand.",
            ),
            Crop(
                name="Chickpea",
                name_hindi="चना",
                scientific_name="Cicer arietinum",
                season="Rabi",
                duration=100,
                water_requirement=35,
                soil_compatibility="black, loamy",
                estimated_yield_min=12,
                estimated_yield_max=15,
                estimated_profit=55000,
                investment_per_acre=20000,
                market_demand_level="high",
                risk_level="low",
                description="Low water rabi pulse crop with steady demand.",
            ),
            Crop(
                name="Maize",
                name_hindi="मक्का",
                scientific_name="Zea mays",
                season="Kharif",
                duration=115,
                water_requirement=58,
                soil_compatibility="loamy, sandy loam",
                estimated_yield_min=25,
                estimated_yield_max=30,
                estimated_profit=72000,
                investment_per_acre=30000,
                market_demand_level="high",
                risk_level="medium",
                description="High-yield kharif crop for farmers with moderate water availability.",
            ),
            Crop(
                name="Mustard",
                name_hindi="सरसों",
                scientific_name="Brassica juncea",
                season="Rabi",
                duration=95,
                water_requirement=30,
                soil_compatibility="alluvial, loamy",
                estimated_yield_min=18,
                estimated_yield_max=20,
                estimated_profit=48000,
                investment_per_acre=18000,
                market_demand_level="medium",
                risk_level="medium",
                description="Oilseed crop with low irrigation needs and decent margins.",
            ),
        ]
        db.add_all(crops)
        db.flush()

        for crop in crops:
            for day_offset, price_offset in zip(range(0, 5), [0, 20, -10, 35, 50], strict=False):
                db.add(
                    MarketPrice(
                        crop_id=crop.id,
                        market_name="Itarsi Mandi",
                        price=max(crop.estimated_profit / 10 + price_offset, 1000),
                        date=datetime.now(UTC) - timedelta(days=4 - day_offset),
                    )
                )

        db.add_all(
            [
                WeatherData(
                    location="Itarsi, Madhya Pradesh",
                    temperature=29,
                    humidity=62,
                    rainfall=1.2,
                    wind_speed=3.4,
                    weather_main="Clouds",
                    weather_description="scattered clouds",
                    weather_icon="03d",
                    recorded_at=datetime.now(UTC),
                ),
                WeatherData(
                    location="Itarsi, Madhya Pradesh",
                    temperature=30,
                    humidity=58,
                    rainfall=0.0,
                    wind_speed=3.1,
                    weather_main="Clear",
                    weather_description="clear sky",
                    weather_icon="01d",
                    recorded_at=datetime.now(UTC) + timedelta(days=1),
                ),
                WeatherData(
                    location="Itarsi, Madhya Pradesh",
                    temperature=28,
                    humidity=65,
                    rainfall=2.0,
                    wind_speed=3.8,
                    weather_main="Rain",
                    weather_description="light rain",
                    weather_icon="10d",
                    recorded_at=datetime.now(UTC) + timedelta(days=2),
                ),
            ]
        )

        demo_user = User(
            email="farmer@example.com",
            phone="+919876543210",
            hashed_password="$2b$12$gM37g8eLQllmBopxkP6P4ejPveDUH0VxjeRGna43EIBgzHuLlHot6",
            full_name="Ramesh Kumar",
            language_preference="hi",
            role="farmer",
            is_active=True,
        )
        db.add(demo_user)
        db.flush()

        demo_farm = Farm(
            name="Ramesh Farm",
            location="Itarsi, Madhya Pradesh",
            area=5.0,
            soil_type="loamy",
            irrigation_type="drip",
            owner_id=demo_user.id,
        )
        db.add(demo_farm)
        db.flush()

        db.add(
            SoilTest(
                farm_id=demo_farm.id,
                ph=6.8,
                nitrogen=45,
                phosphorus=72,
                potassium=58,
                organic_matter=2.6,
                test_date=datetime.now(UTC) - timedelta(days=14),
            )
        )
        db.add_all(
            [
                FarmCropCycle(
                    farm_id=demo_farm.id,
                    crop_id=crops[0].id,
                    season="Kharif",
                    year=date.today().year,
                    sowing_date=date.today() - timedelta(days=50),
                    expected_harvest_date=date.today() + timedelta(days=45),
                    area=4.5,
                    status="active",
                ),
                FarmCropCycle(
                    farm_id=demo_farm.id,
                    crop_id=crops[1].id,
                    season="Rabi",
                    year=date.today().year - 1,
                    sowing_date=date.today() - timedelta(days=450),
                    expected_harvest_date=date.today() - timedelta(days=320),
                    area=5.0,
                    status="completed",
                    yield_achieved=22.8,
                    profit_loss=38000,
                ),
                FarmCropCycle(
                    farm_id=demo_farm.id,
                    crop_id=crops[3].id,
                    season="Kharif",
                    year=date.today().year - 1,
                    sowing_date=date.today() - timedelta(days=700),
                    expected_harvest_date=date.today() - timedelta(days=560),
                    area=4.0,
                    status="completed",
                    yield_achieved=18.5,
                    profit_loss=-8000,
                ),
            ]
        )

        db.commit()

