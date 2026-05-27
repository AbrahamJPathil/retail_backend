from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)


class CustomerCreate(CustomerBase):
    loyalty_points: int = Field(default=0, ge=0)


class CustomerOut(CustomerBase):
    id: int
    loyalty_points: int = Field(default=0, ge=0)
    loyalty_tier: str


class CustomerHistoryItem(BaseModel):
    id: int
    timestamp: str
    payment_method: str
    total_amount: float
    item_count: int


class CustomerHistoryResponse(BaseModel):
    customer_id: int
    purchase_count: int
    total_spent: float
    sales: list[CustomerHistoryItem]
