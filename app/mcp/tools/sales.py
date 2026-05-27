from typing import List, Optional

from app.mcp.server import mcp

from app.schemas.sale import (
    SaleRecord,
    SaleCheckoutRequest,
    SaleReceipt,
    SaleReturnRequest,
    SaleReturnResponse,
)
from app.services import sales as sales_service


@mcp.tool
async def checkout_sale(payload: SaleCheckoutRequest) -> SaleRecord:
    return await sales_service.checkout_sale(payload)


@mcp.tool
async def get_sales_history(date: Optional[str] = None) -> List[SaleRecord]:
    return await sales_service.get_sales_history(date)


@mcp.tool
async def get_sale_receipt(sale_id: int) -> SaleReceipt:
    return await sales_service.get_sale_receipt(sale_id)


@mcp.tool
async def process_sale_return(sale_id: int, payload: SaleReturnRequest) -> SaleReturnResponse:
    return await sales_service.process_sale_return(sale_id, payload)
