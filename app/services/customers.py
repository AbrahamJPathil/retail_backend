"""Customer service functions.

This module contains the canonical business logic for customer-related
operations. Service functions are transport-agnostic and can be called
from HTTP routes or registered as MCP tools. They use the JSON storage
adapter (`app.storage.json_manager`) to persist data in `data/*.json`.
"""

from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.schemas.customer import (
    CustomerCreate,
    CustomerHistoryItem,
    CustomerHistoryResponse,
    CustomerOut,
)
from app.storage.json_manager import read_json, write_json


CUSTOMERS_FILE_PATH = "data/customers.json"
SALES_FILE_PATH = "data/sales.json"


def _resolve_loyalty_tier(points: int) -> str:
    """Return a loyalty tier name for the given points.

    Args:
        points: Loyalty points (non-negative integer).

    Returns:
        A string representing the loyalty tier (Platinum/Gold/Silver/Bronze).
    """
    if points >= 1200:
        return "Platinum"
    if points >= 700:
        return "Gold"
    if points >= 300:
        return "Silver"
    return "Bronze"


def _find_customer_index(customers: list[Dict[str, Any]], customer_id: int) -> int:
    """Find the index of a customer with the given id in a list.

    Args:
        customers: A list of customer dictionaries.
        customer_id: The numeric customer id to locate.

    Returns:
        The list index if found, otherwise -1.
    """
    for index, customer in enumerate(customers):
        if customer.get("id") == customer_id:
            return index
    return -1


def _to_customer_out(customer: Dict[str, Any]) -> CustomerOut:
    """Convert a raw customer dict to `CustomerOut` model.

    Args:
        customer: A dict loaded from storage representing a customer.

    Returns:
        `CustomerOut` model instance with derived `loyalty_tier`.

    Raises:
        HTTPException(500): If the stored customer id is invalid.
    """
    customer_id = customer.get("id")
    if not isinstance(customer_id, int):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid customer data")

    points = int(customer.get("loyalty_points", 0))
    return CustomerOut(
        id=customer_id,
        name=str(customer.get("name", "")),
        phone=str(customer.get("phone", "")),
        email=str(customer.get("email", "")),
        loyalty_points=points,
        loyalty_tier=_resolve_loyalty_tier(points),
    )


async def list_customers(search_phone: str | None = None) -> List[CustomerOut]:
    """List customers, optionally filtering by phone substring.

    Args:
        search_phone: Optional phone substring to filter customers (case-insensitive).

    Returns:
        A list of `CustomerOut` models matching the filter.
    """
    customers = await read_json(CUSTOMERS_FILE_PATH)

    if search_phone:
        query = search_phone.strip().lower()
        customers = [
            customer
            for customer in customers
            if query in str(customer.get("phone", "")).lower()
        ]

    return [_to_customer_out(customer) for customer in customers]


async def register_customer(payload: CustomerCreate) -> CustomerOut:
    """Register a new customer if phone and email are unique.

    Args:
        payload: `CustomerCreate` model containing name, phone, email, and optional loyalty points.

    Returns:
        `CustomerOut` for the newly created customer.

    Raises:
        HTTPException(400): If phone or email already exists.
    Side effects:
        Persists the new customer to `data/customers.json`.
    """
    customers = await read_json(CUSTOMERS_FILE_PATH)

    phone_lower = payload.phone.lower()
    email_lower = payload.email.lower()
    for customer in customers:
        if str(customer.get("phone", "")).lower() == phone_lower:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone already exists")
        if str(customer.get("email", "")).lower() == email_lower:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    existing_ids = [int(customer["id"]) for customer in customers if isinstance(customer.get("id"), int)]
    next_id = (max(existing_ids) + 1) if existing_ids else 1

    new_customer = payload.model_dump()
    new_customer["id"] = next_id

    customers.append(new_customer)
    await write_json(CUSTOMERS_FILE_PATH, customers)

    return _to_customer_out(new_customer)


async def get_customer_profile(customer_id: int) -> CustomerOut:
    """Retrieve a single customer profile by id.

    Args:
        customer_id: Numeric id of the customer to fetch.

    Returns:
        `CustomerOut` for the requested customer.

    Raises:
        HTTPException(404): If the customer is not found.
    """
    customers = await read_json(CUSTOMERS_FILE_PATH)
    customer_index = _find_customer_index(customers, customer_id)

    if customer_index == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return _to_customer_out(customers[customer_index])


async def get_customer_history(customer_id: int) -> CustomerHistoryResponse:
    """Return purchase history summary for a customer.

    Args:
        customer_id: Numeric id of the customer.

    Returns:
        `CustomerHistoryResponse` containing purchase_count, total_spent and a list of sales.

    Raises:
        HTTPException(404): If the customer is not found.
    """
    customers = await read_json(CUSTOMERS_FILE_PATH)
    customer_index = _find_customer_index(customers, customer_id)

    if customer_index == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    sales = await read_json(SALES_FILE_PATH)
    customer_sales = [
        sale
        for sale in sales
        if isinstance(sale.get("customer_id"), int) and sale.get("customer_id") == customer_id
    ]

    history_items: list[CustomerHistoryItem] = []
    total_spent = 0.0

    for sale in customer_sales:
        sale_id = sale.get("id")
        if not isinstance(sale_id, int):
            continue

        items = sale.get("items", [])
        item_count = sum(int(item.get("quantity", 0)) for item in items)
        sale_total = float(sale.get("total_amount", 0.0))
        total_spent += sale_total

        history_items.append(
            CustomerHistoryItem(
                id=sale_id,
                timestamp=str(sale.get("timestamp", "")),
                payment_method=str(sale.get("payment_method", "")),
                total_amount=sale_total,
                item_count=item_count,
            )
        )

    history_items.sort(key=lambda sale: sale.timestamp, reverse=True)

    return CustomerHistoryResponse(
        customer_id=customer_id,
        purchase_count=len(history_items),
        total_spent=round(total_spent, 2),
        sales=history_items,
    )
