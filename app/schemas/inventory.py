from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CATEGORY_VALUES = Literal["fertilizer", "seeds", "pesticide", "equipment", "other"]


class InventoryItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    name_hindi: str = Field(default="", max_length=255)
    category: CATEGORY_VALUES = "other"
    quantity: float = Field(default=0, ge=0)
    unit: str = Field(default="kg", max_length=50)
    low_stock_threshold: float = Field(default=0, ge=0)
    cost: float = Field(default=0, ge=0)
    supplier: str = Field(default="", max_length=255)
    expiry_date: str | None = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    """All fields optional for PATCH-style updates."""
    name: str | None = Field(default=None, max_length=255)
    name_hindi: str | None = Field(default=None, max_length=255)
    category: CATEGORY_VALUES | None = None
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=50)
    low_stock_threshold: float | None = Field(default=None, ge=0)
    cost: float | None = Field(default=None, ge=0)
    supplier: str | None = Field(default=None, max_length=255)
    expiry_date: str | None = None


class InventoryItemRead(InventoryItemBase):
    id: int
    owner_id: int
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InventoryStats(BaseModel):
    total_items: int
    low_stock_count: int
    total_value: float
    categories_count: int
