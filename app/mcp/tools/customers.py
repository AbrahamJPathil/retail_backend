from typing import List, Optional

from app.mcp.server import mcp

from app.schemas.customer import CustomerOut, CustomerCreate, CustomerHistoryResponse
from app.services import customers as customers_service


@mcp.tool
async def list_customers(search_phone: Optional[str] = None) -> List[CustomerOut]:
    return await customers_service.list_customers(search_phone)


@mcp.tool
async def register_customer(payload: CustomerCreate) -> CustomerOut:
    return await customers_service.register_customer(payload)


@mcp.tool
async def get_customer_profile(customer_id: int) -> CustomerOut:
    return await customers_service.get_customer_profile(customer_id)


@mcp.tool
async def get_customer_history(customer_id: int) -> CustomerHistoryResponse:
    return await customers_service.get_customer_history(customer_id)
