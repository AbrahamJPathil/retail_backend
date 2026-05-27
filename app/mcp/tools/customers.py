"""MCP tool wrappers for customer service functions.

Tools here forward requests to `app.services.customers`. Docstrings explain
arguments, return types, possible errors and which storage files are read
or mutated.
"""

from typing import List, Optional

from app.mcp.instance import mcp

from app.schemas.customer import CustomerOut, CustomerCreate, CustomerHistoryResponse
from app.services import customers as customers_service


@mcp.tool
async def list_customers(search_phone: Optional[str] = None) -> List[CustomerOut]:
    """List registered customers optionally filtering by phone substring.

    Args:
        search_phone: Optional substring to match against stored phone numbers.

    Returns:
        List of `CustomerOut` objects.

    Side effects:
        None. Reads from `data/customers.json`.
    """

    return await customers_service.list_customers(search_phone)


@mcp.tool
async def register_customer(payload: CustomerCreate) -> CustomerOut:
    """Register a new customer and persist the record.

    Args:
        payload: `CustomerCreate` payload.

    Returns:
        The created `CustomerOut`.

    Raises:
        HTTPException(400): If a customer with the same phone already exists.

    Side effects:
        Appends the customer to `data/customers.json`.
    """

    return await customers_service.register_customer(payload)


@mcp.tool
async def get_customer_profile(customer_id: int) -> CustomerOut:
    """Return a customer's profile by numeric id.

    Args:
        customer_id: Numeric id of the customer.

    Returns:
        `CustomerOut` for the requested customer.

    Raises:
        HTTPException(404): If the customer does not exist.

    Side effects:
        None. Reads from `data/customers.json`.
    """

    return await customers_service.get_customer_profile(customer_id)


@mcp.tool
async def get_customer_history(customer_id: int) -> CustomerHistoryResponse:
    """Return purchase history and related info for a customer.

    Args:
        customer_id: Numeric id of the customer whose history to fetch.

    Returns:
        `CustomerHistoryResponse` containing customer details and sales list.

    Raises:
        HTTPException(404): If the customer does not exist.

    Side effects:
        Reads from `data/customers.json` and `data/sales.json`.
    """

    return await customers_service.get_customer_history(customer_id)
