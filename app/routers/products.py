from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.product import ProductCreate, ProductOut, ProductPut, ProductStockPatch
from app.storage.json_manager import read_json, write_json

router = APIRouter(prefix="/products", tags=["Products"])

PRODUCTS_FILE_PATH = "data/products.json"
LOW_STOCK_THRESHOLD = 10


def _is_active(product: Dict[str, Any]) -> bool:
	return product.get("active", True)


def _match_product_identifier(product: Dict[str, Any], product_id: str) -> bool:
	if product_id.isdigit() and product.get("id") == int(product_id):
		return True
	return str(product.get("sku", "")).lower() == product_id.lower()


def _find_product_index(products: List[Dict[str, Any]], product_id: str) -> int:
	for index, product in enumerate(products):
		if _is_active(product) and _match_product_identifier(product, product_id):
			return index
	return -1


@router.get("/", response_model=List[ProductOut])
async def list_products(
	category: str | None = Query(default=None),
	low_stock: bool = Query(default=False),
) -> List[ProductOut]:
	products = await read_json(PRODUCTS_FILE_PATH)

	filtered = [product for product in products if _is_active(product)]

	if category:
		filtered = [
			product
			for product in filtered
			if str(product.get("category", "")).lower() == category.lower()
		]

	if low_stock:
		filtered = [
			product
			for product in filtered
			if int(product.get("stock_quantity", 0)) <= LOW_STOCK_THRESHOLD
		]

	return [ProductOut.model_validate(product) for product in filtered]


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate) -> ProductOut:
	products = await read_json(PRODUCTS_FILE_PATH)

	sku_lower = payload.sku.lower()
	if any(str(product.get("sku", "")).lower() == sku_lower for product in products if _is_active(product)):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SKU already exists")

	existing_ids = [int(product["id"]) for product in products if isinstance(product.get("id"), int)]
	next_id = (max(existing_ids) + 1) if existing_ids else 1

	new_product = payload.model_dump()
	new_product["id"] = next_id
	new_product["active"] = True

	products.append(new_product)
	await write_json(PRODUCTS_FILE_PATH, products)

	return ProductOut.model_validate(new_product)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: str) -> ProductOut:
	products = await read_json(PRODUCTS_FILE_PATH)
	index = _find_product_index(products, product_id)

	if index == -1:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

	return ProductOut.model_validate(products[index])


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, payload: ProductPut) -> ProductOut:
	products = await read_json(PRODUCTS_FILE_PATH)
	index = _find_product_index(products, product_id)

	if index == -1:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

	current = products[index]
	update_data = payload.model_dump(exclude_none=True)

	if "sku" in update_data:
		new_sku = str(update_data["sku"]).lower()
		duplicate_sku_exists = any(
			i != index and _is_active(product) and str(product.get("sku", "")).lower() == new_sku
			for i, product in enumerate(products)
		)
		if duplicate_sku_exists:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SKU already exists")

	current.update(update_data)
	products[index] = current

	await write_json(PRODUCTS_FILE_PATH, products)
	return ProductOut.model_validate(products[index])


@router.patch("/{product_id}/stock", response_model=ProductOut)
async def patch_product_stock(product_id: str, payload: ProductStockPatch) -> ProductOut:
	products = await read_json(PRODUCTS_FILE_PATH)
	index = _find_product_index(products, product_id)

	if index == -1:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

	current_stock = int(products[index].get("stock_quantity", 0))
	updated_stock = current_stock + payload.quantity_change

	if updated_stock < 0:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Stock update would result in negative quantity",
		)

	products[index]["stock_quantity"] = updated_stock
	await write_json(PRODUCTS_FILE_PATH, products)

	return ProductOut.model_validate(products[index])


@router.delete("/{product_id}")
async def delete_or_archive_product(
	product_id: str,
	archive: bool = Query(default=True),
) -> Dict[str, str]:
	products = await read_json(PRODUCTS_FILE_PATH)
	index = _find_product_index(products, product_id)

	if index == -1:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

	if archive:
		products[index]["active"] = False
		await write_json(PRODUCTS_FILE_PATH, products)
		return {"message": "Product archived successfully"}

	products.pop(index)
	await write_json(PRODUCTS_FILE_PATH, products)
	return {"message": "Product deleted successfully"}
