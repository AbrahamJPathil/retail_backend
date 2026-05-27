from typing import Optional

from pydantic import BaseModel, Field


class SaleCheckoutItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class SaleCheckoutRequest(BaseModel):
    customer_id: Optional[int] = Field(default=None, gt=0)
    items: list[SaleCheckoutItem] = Field(..., min_length=1)
    payment_method: str = Field(..., min_length=1)


class SaleRecordItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class SaleRecord(BaseModel):
    id: int
    customer_id: Optional[int] = None
    timestamp: str
    items: list[SaleRecordItem]
    payment_method: str
    total_amount: float


class SaleReturnItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class SaleReturnRequest(BaseModel):
    items: list[SaleReturnItem] = Field(..., min_length=1)


class ReturnedItemSummary(BaseModel):
    product_id: int
    quantity: int
    refunded_amount: float


class SaleReturnResponse(BaseModel):
    sale_id: int
    returned_items: list[ReturnedItemSummary]
    total_refunded: float


class ReceiptItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    line_total: float


class SaleReceipt(BaseModel):
    id: int
    customer_id: Optional[int] = None
    timestamp: str
    payment_method: str
    items: list[ReceiptItem]
    total_amount: float
