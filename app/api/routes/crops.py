from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.crop import Crop, ManagedCrop
from app.models.farm import Farm
from app.models.user import User
from app.schemas.crop import (
    CropRead,
    CropRecommendationItem,
    CropRecommendationRequest,
    ManagedCropCreate,
    ManagedCropRead,
    ManagedCropUpdate,
)
from app.services.crop_recommendation import recommend_crops_dynamic


router = APIRouter()


def _serialize_managed_crop(item: ManagedCrop) -> ManagedCropRead:
    return ManagedCropRead(
        id=item.id,
        farm_id=item.farm_id,
        farm_name=item.farm.name,
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


def _get_owned_farm(db: Session, user_id: int, farm_id: int) -> Farm:
    farm = db.scalar(select(Farm).where(Farm.id == farm_id, Farm.owner_id == user_id))
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


def _get_owned_managed_crop(db: Session, user_id: int, crop_id: int) -> ManagedCrop:
    crop = db.execute(
        select(ManagedCrop)
        .join(Farm, ManagedCrop.farm_id == Farm.id)
        .options(joinedload(ManagedCrop.farm))
        .where(ManagedCrop.id == crop_id, Farm.owner_id == user_id)
    ).scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Managed crop not found")
    return crop


def _normalize_active_status(db: Session, farm_id: int, active_crop_id: int | None = None) -> None:
    active_crops = list(
        db.scalars(
            select(ManagedCrop).where(
                ManagedCrop.farm_id == farm_id,
                ManagedCrop.status == "active",
            )
        )
    )
    for crop in active_crops:
        if active_crop_id is not None and crop.id == active_crop_id:
            continue
        crop.status = "planned"
        db.add(crop)


@router.get("", response_model=list[CropRead])
def list_crops(db: Session = Depends(get_db)) -> list[Crop]:
    return list(db.scalars(select(Crop).order_by(Crop.name.asc())))


@router.get("/managed", response_model=list[ManagedCropRead])
def list_managed_crops(
    farm_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ManagedCropRead]:
    query = (
        select(ManagedCrop)
        .join(Farm, ManagedCrop.farm_id == Farm.id)
        .options(joinedload(ManagedCrop.farm))
        .where(Farm.owner_id == current_user.id)
        .order_by(ManagedCrop.updated_at.desc(), ManagedCrop.created_at.desc())
    )
    if farm_id is not None:
        query = query.where(ManagedCrop.farm_id == farm_id)

    items = list(db.execute(query).scalars())
    return [_serialize_managed_crop(item) for item in items]


@router.post("/managed", response_model=ManagedCropRead, status_code=status.HTTP_201_CREATED)
def create_managed_crop(
    payload: ManagedCropCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ManagedCropRead:
    _get_owned_farm(db, current_user.id, payload.farm_id)
    item = ManagedCrop(**payload.model_dump())
    db.add(item)
    db.flush()

    if item.status == "active":
        _normalize_active_status(db, item.farm_id, item.id)

    db.commit()
    item = _get_owned_managed_crop(db, current_user.id, item.id)
    return _serialize_managed_crop(item)


@router.put("/managed/{crop_id}", response_model=ManagedCropRead)
def update_managed_crop(
    crop_id: int,
    payload: ManagedCropUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ManagedCropRead:
    item = _get_owned_managed_crop(db, current_user.id, crop_id)
    changes = payload.model_dump(exclude_unset=True)

    if "farm_id" in changes and changes["farm_id"] is not None and changes["farm_id"] != item.farm_id:
        _get_owned_farm(db, current_user.id, changes["farm_id"])

    for field, value in changes.items():
        setattr(item, field, value)
    db.add(item)
    db.flush()

    if item.status == "active":
        _normalize_active_status(db, item.farm_id, item.id)

    db.commit()
    item = _get_owned_managed_crop(db, current_user.id, crop_id)
    return _serialize_managed_crop(item)


@router.post("/recommendation", response_model=list[CropRecommendationItem])
def recommend_crops(
    payload: CropRecommendationRequest, db: Session = Depends(get_db)
) -> list[CropRecommendationItem]:
    return recommend_crops_dynamic(db, payload)
