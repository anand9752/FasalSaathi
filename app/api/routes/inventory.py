from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.inventory import InventoryItem
from app.models.user import User
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemRead,
    InventoryItemUpdate,
    InventoryStats,
)


router = APIRouter()


def _serialize(item: InventoryItem) -> InventoryItemRead:
    return InventoryItemRead(
        id=item.id,
        owner_id=item.owner_id,
        name=item.name,
        name_hindi=item.name_hindi,
        category=item.category,  # type: ignore[arg-type]
        quantity=item.quantity,
        unit=item.unit,
        low_stock_threshold=item.low_stock_threshold,
        cost=item.cost,
        supplier=item.supplier,
        expiry_date=item.expiry_date,
        is_low_stock=item.quantity <= item.low_stock_threshold,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _get_owned(db: Session, user_id: int, item_id: int) -> InventoryItem:
    item = db.scalars(
        select(InventoryItem)
        .where(InventoryItem.id == item_id, InventoryItem.owner_id == user_id)
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    return item


# ── routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[InventoryItemRead])
def list_inventory(
    category: str | None = Query(default=None),
    low_stock_only: bool = Query(default=False),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[InventoryItemRead]:
    """List all inventory items for the current user with optional filters."""
    stmt = select(InventoryItem).where(InventoryItem.owner_id == current_user.id)
    if category and category != "all":
        stmt = stmt.where(InventoryItem.category == category)
    stmt = stmt.order_by(InventoryItem.updated_at.desc())
    items = list(db.scalars(stmt))

    results = [_serialize(i) for i in items]

    if low_stock_only:
        results = [r for r in results if r.is_low_stock]
    if search:
        s = search.lower()
        results = [r for r in results if s in r.name.lower() or s in r.name_hindi.lower()]

    return results


@router.post("", response_model=InventoryItemRead, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InventoryItemRead:
    """Add a new inventory item."""
    item = InventoryItem(owner_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize(item)


@router.get("/stats", response_model=InventoryStats)
def get_inventory_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InventoryStats:
    """Summary stats: total items, low-stock count, total value, unique category count."""
    items = list(db.scalars(
        select(InventoryItem).where(InventoryItem.owner_id == current_user.id)
    ))
    low_stock = [i for i in items if i.quantity <= i.low_stock_threshold]
    total_value = sum(i.cost * i.quantity for i in items)
    categories = {i.category for i in items}
    return InventoryStats(
        total_items=len(items),
        low_stock_count=len(low_stock),
        total_value=total_value,
        categories_count=len(categories),
    )


@router.get("/{item_id}", response_model=InventoryItemRead)
def get_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InventoryItemRead:
    return _serialize(_get_owned(db, current_user.id, item_id))


@router.put("/{item_id}", response_model=InventoryItemRead)
def update_inventory_item(
    item_id: int,
    payload: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InventoryItemRead:
    """Full or partial update of an inventory item."""
    item = _get_owned(db, current_user.id, item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete an inventory item."""
    item = _get_owned(db, current_user.id, item_id)
    db.delete(item)
    db.commit()
