from typing import List

from fastapi import APIRouter, Query

from app.schemas.customer import (
	CustomerCreate,
	CustomerHistoryResponse,
	CustomerOut,
)
from app.services import customers as customers_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=List[CustomerOut])
async def list_customers(search_phone: str | None = Query(default=None)) -> List[CustomerOut]:
	return await customers_service.list_customers(search_phone)


@router.post("/", response_model=CustomerOut, status_code=201)
async def register_customer(payload: CustomerCreate) -> CustomerOut:
	return await customers_service.register_customer(payload)


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer_profile(customer_id: int) -> CustomerOut:
	return await customers_service.get_customer_profile(customer_id)


@router.get("/{customer_id}/history", response_model=CustomerHistoryResponse)
async def get_customer_history(customer_id: int) -> CustomerHistoryResponse:
	return await customers_service.get_customer_history(customer_id)
