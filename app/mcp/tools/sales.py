"""MCP tool wrappers for sales service functions.

Each tool delegates to `app.services.sales`. Docstrings enumerate the
expected payloads, return types, errors and any storage side-effects.
"""

from typing import List, Optional

from app.mcp.instance import mcp

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
    """Process a checkout, decrement inventory and record the sale.

    Args:
        payload: `SaleCheckoutRequest` with `items`, optional `customer_id`, and `payment_method`.

    Returns:
        `SaleRecord` for the created sale.

    Raises:
        HTTPException(404): If a referenced product is not found.
        HTTPException(400): If requested quantity exceeds available stock.

    Side effects:
        Mutates `data/products.json` (stock) and appends to `data/sales.json`.
    """

    return await sales_service.checkout_sale(payload)


@mcp.tool
async def get_sales_history(date: Optional[str] = None) -> List[SaleRecord]:
    """Return sales ledger entries, optionally filtered by date prefix YYYY-MM-DD.

    Args:
        date: Optional date string to filter sales by timestamp prefix.

    Returns:
        List of `SaleRecord` objects.

    Raises:
        HTTPException(400): If `date` is not a valid YYYY-MM-DD string.

    Side effects:
        None. Reads from `data/sales.json`.
    """

    return await sales_service.get_sales_history(date)


@mcp.tool
async def get_sale_receipt(sale_id: int) -> SaleReceipt:
    """Return a formatted receipt for a sale, including item names and totals.

    Args:
        sale_id: Numeric id of the sale.

    Returns:
        `SaleReceipt` with itemized lines and totals.

    Raises:
        HTTPException(404): If the sale is not found.

    Side effects:
        Reads from `data/sales.json` and `data/products.json`.
    """

    return await sales_service.get_sale_receipt(sale_id)


@mcp.tool
async def process_sale_return(sale_id: int, payload: SaleReturnRequest) -> SaleReturnResponse:
    """Process a return for a previously recorded sale.

    Args:
        sale_id: Numeric id of the sale.
        payload: `SaleReturnRequest` listing returned product ids and quantities.

    Returns:
        `SaleReturnResponse` summarizing refunded items and amount.

    Raises:
        HTTPException(404): If the sale or referenced product cannot be found.
        HTTPException(400): If the return quantity exceeds what was sold and not yet returned.

    Side effects:
        Restores product stock in `data/products.json` and appends return events to `data/sales.json`.
    """

    return await sales_service.process_sale_return(sale_id, payload)
