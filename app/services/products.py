"""Product service functions.

This module implements product catalog and inventory business logic.
Service functions are used by HTTP routes and MCP tools and persist state
in `data/products.json` via the JSON manager.
"""

from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.schemas.product import ProductCreate, ProductOut, ProductPut, ProductStockPatch
from app.storage.json_manager import read_json, write_json

PRODUCTS_FILE_PATH = "data/products.json"
LOW_STOCK_THRESHOLD = 10


def _is_active(product: Dict[str, Any]) -> bool:
    """Return True if product is active (not archived)."""
    return product.get("active", True)


def _match_product_identifier(product: Dict[str, Any], product_id: str) -> bool:
    """Return True if the product matches the given identifier.

    The identifier can be a numeric id string or a SKU.
    """
    if product_id.isdigit() and product.get("id") == int(product_id):
        return True
    return str(product.get("sku", "")).lower() == product_id.lower()


def _find_product_index(products: List[Dict[str, Any]], product_id: str) -> int:
    """Find the index of an active product matching `product_id`.

    Args:
        products: List of product dicts loaded from storage.
        product_id: SKU or numeric id (as string) to match.

    Returns:
        Index of the matching product or -1 if not found.
    """
    for index, product in enumerate(products):
        if _is_active(product) and _match_product_identifier(product, product_id):
            return index
    return -1


async def list_products(category: str | None = None, low_stock: bool = False) -> List[ProductOut]:
    """List active products optionally filtered by category or low-stock.

    Args:
        category: Optional category name to filter (case-insensitive).
        low_stock: If True, only return products with stock_quantity <= LOW_STOCK_THRESHOLD.

    Returns:
        List of `ProductOut` models representing matching products.
    """
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


async def create_product(payload: ProductCreate) -> ProductOut:
    """Create a new product and persist it.

    Args:
        payload: `ProductCreate` containing product fields.

    Returns:
        `ProductOut` for the created product.

    Raises:
        HTTPException(400): If the SKU already exists for an active product.
    """
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


async def get_product(product_id: str) -> ProductOut:
    """Return a single product by SKU or numeric id string.

    Args:
        product_id: SKU or numeric id (as string).

    Returns:
        `ProductOut` for the matched product.

    Raises:
        HTTPException(404): If the product is not found or not active.
    """
    products = await read_json(PRODUCTS_FILE_PATH)
    index = _find_product_index(products, product_id)

    if index == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return ProductOut.model_validate(products[index])


async def update_product(product_id: str, payload: ProductPut) -> ProductOut:
    """Update mutable product fields.

    Args:
        product_id: SKU or numeric id (as string) to identify the product.
        payload: `ProductPut` with fields to update.

    Returns:
        Updated `ProductOut` model.

    Raises:
        HTTPException(404): If product not found.
        HTTPException(400): If the new SKU collides with another active product.
    """
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


async def patch_product_stock(product_id: str, payload: ProductStockPatch) -> ProductOut:
    """Adjust the stock quantity for a product by a signed integer delta.

    Args:
        product_id: SKU or numeric id (as string) identifying the product.
        payload: `ProductStockPatch` with `quantity_change` which may be negative.

    Returns:
        Updated `ProductOut` model.

    Raises:
        HTTPException(404): If product not found.
        HTTPException(400): If the update would result in negative stock.
    Side effects:
        Persists updated stock to `data/products.json`.
    """
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


async def delete_or_archive_product(product_id: str, archive: bool = True) -> Dict[str, str]:
    """Archive or permanently delete a product.

    Args:
        product_id: SKU or numeric id (as string).
        archive: If True, set the product's active flag to False; otherwise remove it from storage.

    Returns:
        A dict with a `message` describing the performed action.

    Raises:
        HTTPException(404): If the product is not found.
    """
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
