from typing import List

from fastapi import APIRouter, Query

from app.schemas.sale import (
	SaleCheckoutRequest,
	SaleReceipt,
	SaleRecord,
	SaleReturnRequest,
	SaleReturnResponse,
)
from app.services import sales as sales_service

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("/", response_model=SaleRecord, status_code=201)
async def checkout_sale(payload: SaleCheckoutRequest) -> SaleRecord:
	return await sales_service.checkout_sale(payload)


@router.get("/", response_model=list[SaleRecord])
async def get_sales_history(date: str | None = Query(default=None)) -> list[SaleRecord]:
	return await sales_service.get_sales_history(date)


@router.get("/{sale_id}", response_model=SaleReceipt)
async def get_sale_receipt(sale_id: int) -> SaleReceipt:
	return await sales_service.get_sale_receipt(sale_id)


@router.post("/{sale_id}/return", response_model=SaleReturnResponse)
async def process_sale_return(sale_id: int, payload: SaleReturnRequest) -> SaleReturnResponse:
	return await sales_service.process_sale_return(sale_id, payload)
