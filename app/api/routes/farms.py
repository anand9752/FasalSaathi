from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.crop import Crop, FarmCropCycle
from app.models.farm import Farm
from app.models.user import User
from app.schemas.crop import ManagedCropRead
from app.schemas.farm import CropCycleRead, FarmCreate, FarmRead, FarmUpdate, SoilTestRead


def _serialize_farm(farm: Farm) -> FarmRead:
    return FarmRead(
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
        crop_cycles=[
            CropCycleRead(
                id=item.id,
                crop_id=item.crop_id,
                crop_name=item.crop.name,
                crop_name_hindi=item.crop.name_hindi,
                season=item.season,
                year=item.year,
                sowing_date=item.sowing_date,
                expected_harvest_date=item.expected_harvest_date,
                area=item.area,
                status=item.status,
                yield_achieved=item.yield_achieved,
                profit_loss=item.profit_loss,
            )
            for item in sorted(farm.crop_cycles, key=lambda x: (x.year, x.created_at), reverse=True)
        ],
        managed_crops=[
            ManagedCropRead(
                id=item.id,
                farm_id=item.farm_id,
                farm_name=farm.name,
                name=item.name,
                name_hindi=item.name_hindi,
                crop_type=item.crop_type,
                season=item.season,
                duration=item.duration,
                area=item.area,
                estimated_cost=item.estimated_cost,
                estimated_profit=item.estimated_profit,
                expected_yield=item.expected_yield,
                risk_level=item.risk_level,
                status=item.status,
                sowing_date=item.sowing_date,
                expected_harvest_date=item.expected_harvest_date,
                actual_harvest_date=item.actual_harvest_date,
                variety=item.variety,
                water_requirement=item.water_requirement,
                soil_preference=item.soil_preference,
                description=item.description,
                notes=item.notes,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in sorted(farm.managed_crops, key=lambda x: (x.updated_at, x.created_at), reverse=True)
        ],
    )


router = APIRouter()


def _get_owned_farm(db: Session, user_id: int, farm_id: int) -> Farm:
    farm = db.execute(
        select(Farm)
        .options(
            joinedload(Farm.soil_tests),
            joinedload(Farm.crop_cycles).joinedload(FarmCropCycle.crop),
            joinedload(Farm.managed_crops),
        )
        .where(Farm.id == farm_id, Farm.owner_id == user_id)
    )
    farm = farm.unique().scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


@router.get("", response_model=list[FarmRead])
def list_farms(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> list[FarmRead]:
    farms = list(
        db.execute(
            select(Farm)
            .options(
                joinedload(Farm.soil_tests),
                joinedload(Farm.crop_cycles).joinedload(FarmCropCycle.crop),
                joinedload(Farm.managed_crops),
            )
            .where(Farm.owner_id == current_user.id)
            .order_by(Farm.created_at.asc())
        )
        .unique()
        .scalars()
    )
    return [_serialize_farm(farm) for farm in farms]


@router.post("", response_model=FarmRead, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FarmRead:
    farm = Farm(owner_id=current_user.id, **payload.model_dump(exclude={"initial_crop_id", "initial_crop_season", "initial_crop_year"}))
    db.add(farm)
    db.flush()

    if payload.initial_crop_id:
        crop = db.get(Crop, payload.initial_crop_id)
        if crop:
            db.add(
                FarmCropCycle(
                    farm_id=farm.id,
                    crop_id=crop.id,
                    season=payload.initial_crop_season or crop.season,
                    year=payload.initial_crop_year or date.today().year,
                    area=payload.area,
                    status="active",
                )
            )
    db.commit()
    farm = _get_owned_farm(db, current_user.id, farm.id)
    return _serialize_farm(farm)


@router.get("/{farm_id}", response_model=FarmRead)
def get_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FarmRead:
    return _serialize_farm(_get_owned_farm(db, current_user.id, farm_id))


@router.put("/{farm_id}", response_model=FarmRead)
def update_farm(
    farm_id: int,
    payload: FarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FarmRead:
    farm = _get_owned_farm(db, current_user.id, farm_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm, field, value)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    farm = _get_owned_farm(db, current_user.id, farm_id)
    return _serialize_farm(farm)


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    farm = _get_owned_farm(db, current_user.id, farm_id)
    db.delete(farm)
    db.commit()


@router.get("/{farm_id}/soil-tests", response_model=list[SoilTestRead])
def get_soil_tests(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SoilTestRead]:
    farm = _get_owned_farm(db, current_user.id, farm_id)
    return [SoilTestRead.model_validate(item) for item in sorted(farm.soil_tests, key=lambda x: x.test_date, reverse=True)]
