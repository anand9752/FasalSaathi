from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.farm import Farm, SoilTest
from app.models.user import User
from app.schemas.farm import SoilTestCreate


def get_owned_farm(db: Session, farm_id: int, current_user: User) -> Farm | None:
    return db.scalar(select(Farm).where(Farm.id == farm_id, Farm.owner_id == current_user.id))


def create_soil_test(db: Session, current_user: User, payload: SoilTestCreate) -> SoilTest:
    farm = get_owned_farm(db, payload.farm_id, current_user)
    if not farm:
        raise ValueError("Farm not found")

    soil_test = SoilTest(
        farm_id=payload.farm_id,
        ph=payload.soil_ph,
        nitrogen=payload.nitrogen,
        phosphorus=payload.phosphorus,
        potassium=payload.potassium,
        organic_matter=0,
        soil_moisture=payload.soil_moisture,
        temperature=payload.temperature,
    )
    db.add(soil_test)
    db.commit()
    db.refresh(soil_test)
    return soil_test


def get_latest_soil_test(db: Session, farm_id: int, current_user: User) -> SoilTest | None:
    farm = get_owned_farm(db, farm_id, current_user)
    if not farm:
        return None

    return db.scalars(
        select(SoilTest)
        .where(SoilTest.farm_id == farm_id)
        .order_by(SoilTest.test_date.desc(), SoilTest.created_at.desc())
    ).first()
