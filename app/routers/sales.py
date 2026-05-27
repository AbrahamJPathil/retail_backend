from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.sale import (
	ReceiptItem,
	SaleCheckoutRequest,
	SaleReceipt,
	SaleRecord,
	SaleReturnRequest,
	SaleReturnResponse,
)
from app.storage.json_manager import read_json, write_json

router = APIRouter(prefix="/sales", tags=["Sales"])

PRODUCTS_FILE_PATH = "data/products.json"
SALES_FILE_PATH = "data/sales.json"


def _find_product_index(products: list[Dict[str, Any]], product_id: int) -> int:
	for index, product in enumerate(products):
		if product.get("id") == product_id and product.get("active", True):
			return index
	return -1


def _find_sale_index(sales: list[Dict[str, Any]], sale_id: int) -> int:
	for index, sale in enumerate(sales):
		if sale.get("id") == sale_id:
			return index
	return -1


def _utc_now_iso() -> str:
	return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@router.post("/", response_model=SaleRecord, status_code=status.HTTP_201_CREATED)
async def checkout_sale(payload: SaleCheckoutRequest) -> SaleRecord:
	products = await read_json(PRODUCTS_FILE_PATH)
	sales = await read_json(SALES_FILE_PATH)

	working_products = [dict(product) for product in products]
	sale_items: list[Dict[str, Any]] = []
	total_amount = 0.0

	for item in payload.items:
		product_index = _find_product_index(working_products, item.product_id)
		if product_index == -1:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail=f"Product {item.product_id} not found",
			)

		product = working_products[product_index]
		current_stock = int(product.get("stock_quantity", 0))
		if current_stock < item.quantity:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"Insufficient stock for product {item.product_id}",
			)

		unit_price = float(product.get("price", 0.0))
		working_products[product_index]["stock_quantity"] = current_stock - item.quantity

		sale_items.append(
			{
				"product_id": item.product_id,
				"quantity": item.quantity,
				"unit_price": unit_price,
			}
		)
		total_amount += unit_price * item.quantity

	existing_sale_ids = [int(sale["id"]) for sale in sales if isinstance(sale.get("id"), int)]
	next_sale_id = (max(existing_sale_ids) + 1) if existing_sale_ids else 1

	new_sale = {
		"id": next_sale_id,
		"customer_id": payload.customer_id,
		"timestamp": _utc_now_iso(),
		"items": sale_items,
		"payment_method": payload.payment_method,
		"total_amount": round(total_amount, 2),
	}

	sales.append(new_sale)

	await write_json(PRODUCTS_FILE_PATH, working_products)
	await write_json(SALES_FILE_PATH, sales)

	return SaleRecord.model_validate(new_sale)


@router.get("/", response_model=list[SaleRecord])
async def get_sales_history(date: str | None = Query(default=None)) -> list[SaleRecord]:
	sales = await read_json(SALES_FILE_PATH)

	if date is not None:
		try:
			datetime.strptime(date, "%Y-%m-%d")
		except ValueError as exc:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Invalid date format. Use YYYY-MM-DD",
			) from exc

		sales = [sale for sale in sales if str(sale.get("timestamp", "")).startswith(date)]

	return [SaleRecord.model_validate(sale) for sale in sales]


@router.get("/{sale_id}", response_model=SaleReceipt)
async def get_sale_receipt(sale_id: int) -> SaleReceipt:
	sales = await read_json(SALES_FILE_PATH)
	products = await read_json(PRODUCTS_FILE_PATH)

	sale_index = _find_sale_index(sales, sale_id)
	if sale_index == -1:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

	product_name_map = {
		int(product["id"]): str(product.get("name", "Unknown Product"))
		for product in products
		if isinstance(product.get("id"), int)
	}

	sale = sales[sale_index]
	receipt_items: list[ReceiptItem] = []
	for item in sale.get("items", []):
		product_id = int(item.get("product_id"))
		quantity = int(item.get("quantity", 0))
		unit_price = float(item.get("unit_price", 0.0))
		receipt_items.append(
			ReceiptItem(
				product_id=product_id,
				product_name=product_name_map.get(product_id, "Unknown Product"),
				quantity=quantity,
				unit_price=unit_price,
				line_total=round(unit_price * quantity, 2),
			)
		)

	return SaleReceipt(
		id=sale_id,
		customer_id=sale.get("customer_id"),
		timestamp=str(sale.get("timestamp")),
		payment_method=str(sale.get("payment_method", "")),
		items=receipt_items,
		total_amount=float(sale.get("total_amount", 0.0)),
	)


@router.post("/{sale_id}/return", response_model=SaleReturnResponse)
async def process_sale_return(sale_id: int, payload: SaleReturnRequest) -> SaleReturnResponse:
	sales = await read_json(SALES_FILE_PATH)
	products = await read_json(PRODUCTS_FILE_PATH)

	sale_index = _find_sale_index(sales, sale_id)
	if sale_index == -1:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

	sale = sales[sale_index]
	sale_items = sale.get("items", [])
	sale_item_map: Dict[int, Dict[str, Any]] = {
		int(item.get("product_id")): item for item in sale_items if item.get("product_id") is not None
	}

	prior_returns = sale.get("returns", [])
	already_returned_map: Dict[int, int] = {}
	for return_event in prior_returns:
		for return_item in return_event.get("items", []):
			product_id = int(return_item.get("product_id"))
			quantity = int(return_item.get("quantity", 0))
			already_returned_map[product_id] = already_returned_map.get(product_id, 0) + quantity

	returned_items_output = []
	return_log_items = []
	total_refunded = 0.0

	for return_item in payload.items:
		if return_item.product_id not in sale_item_map:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"Product {return_item.product_id} is not part of sale {sale_id}",
			)

		sold_quantity = int(sale_item_map[return_item.product_id].get("quantity", 0))
		returned_so_far = already_returned_map.get(return_item.product_id, 0)
		available_for_return = sold_quantity - returned_so_far
		if return_item.quantity > available_for_return:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=(
					f"Cannot return {return_item.quantity} of product {return_item.product_id}. "
					f"Only {available_for_return} available for return"
				),
			)

		product_index = _find_product_index(products, return_item.product_id)
		if product_index == -1:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail=f"Product {return_item.product_id} not found for restocking",
			)

		products[product_index]["stock_quantity"] = int(products[product_index].get("stock_quantity", 0)) + return_item.quantity

		unit_price = float(sale_item_map[return_item.product_id].get("unit_price", 0.0))
		refunded_amount = round(unit_price * return_item.quantity, 2)
		total_refunded += refunded_amount

		returned_items_output.append(
			{
				"product_id": return_item.product_id,
				"quantity": return_item.quantity,
				"refunded_amount": refunded_amount,
			}
		)
		return_log_items.append(
			{
				"product_id": return_item.product_id,
				"quantity": return_item.quantity,
				"unit_price": unit_price,
			}
		)

	return_event = {
		"timestamp": _utc_now_iso(),
		"items": return_log_items,
		"total_refunded": round(total_refunded, 2),
	}
	sale.setdefault("returns", []).append(return_event)
	sales[sale_index] = sale

	await write_json(PRODUCTS_FILE_PATH, products)
	await write_json(SALES_FILE_PATH, sales)

	return SaleReturnResponse(
		sale_id=sale_id,
		returned_items=returned_items_output,
		total_refunded=round(total_refunded, 2),
	)
