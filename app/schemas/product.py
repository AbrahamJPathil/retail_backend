from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1)
    sku: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    cost_price: float = Field(..., ge=0)
    stock_quantity: int = Field(..., ge=0)
    supplier_info: Optional[Dict[str, Any]] = None


class ProductCreate(ProductBase):
    pass


class ProductPut(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    supplier_info: Optional[Dict[str, Any]] = None
    sku: Optional[str] = Field(default=None, min_length=1)
    category: Optional[str] = Field(default=None, min_length=1)
    cost_price: Optional[float] = Field(default=None, ge=0)


class ProductStockPatch(BaseModel):
    quantity_change: int


class ProductOut(ProductBase):
    id: int
    active: bool = True
