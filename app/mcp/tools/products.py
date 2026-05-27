"""MCP tool wrappers for product service functions.

Each function is registered as an MCP tool and forwards calls to the
transport-agnostic service implementation in `app.services.products`.
Tool docstrings describe expected arguments, return types, possible
errors and any storage side-effects (which files may be mutated).
"""

from typing import List, Optional

from app.mcp.instance import mcp

from app.schemas.product import ProductOut, ProductCreate, ProductPut, ProductStockPatch
from app.services import products as products_service


@mcp.tool
async def list_products(category: Optional[str] = None, low_stock: bool = False) -> List[ProductOut]:
    """Return active products, optionally filtered.

    Args:
        category: Optional case-insensitive category name to filter.
        low_stock: If True, restrict results to low-stock items.

    Returns:
        List of `ProductOut` objects.

    Side effects:
        None. Reads from `data/products.json`.
    """

    return await products_service.list_products(category=category, low_stock=low_stock)


@mcp.tool
async def create_product(payload: ProductCreate) -> ProductOut:
    """Create a product in the catalog.

    Args:
        payload: `ProductCreate` payload with product fields.

    Returns:
        The created `ProductOut`.

    Raises:
        HTTPException(400): If the SKU already exists.

    Side effects:
        Mutates `data/products.json` by appending the new product.
    """

    return await products_service.create_product(payload)


@mcp.tool
async def get_product(product_id: str) -> ProductOut:
    """Retrieve a single product by SKU or numeric id string.

    Args:
        product_id: SKU or numeric id (as string).

    Returns:
        `ProductOut` for the matched product.

    Raises:
        HTTPException(404): If the product is not found.

    Side effects:
        None. Reads from `data/products.json`.
    """

    return await products_service.get_product(product_id)


@mcp.tool
async def update_product(product_id: str, payload: ProductPut) -> ProductOut:
    """Update mutable fields on a product.

    Args:
        product_id: SKU or numeric id (as string) identifying the product.
        payload: `ProductPut` payload with fields to change.

    Returns:
        Updated `ProductOut`.

    Raises:
        HTTPException(404): If the product is not found.
        HTTPException(400): If the new SKU conflicts with another active product.

    Side effects:
        Persists changes to `data/products.json`.
    """

    return await products_service.update_product(product_id, payload)


@mcp.tool
async def patch_product_stock(product_id: str, payload: ProductStockPatch) -> ProductOut:
    """Adjust a product's stock by a signed integer delta.

    Args:
        product_id: SKU or numeric id (as string).
        payload: `ProductStockPatch` with `quantity_change` (may be negative).

    Returns:
        Updated `ProductOut`.

    Raises:
        HTTPException(404): If the product is not found.
        HTTPException(400): If the update would make stock negative.

    Side effects:
        Persists updated `stock_quantity` to `data/products.json`.
    """

    return await products_service.patch_product_stock(product_id, payload)


@mcp.tool
async def delete_or_archive_product(product_id: str, archive: bool = True) -> dict:
    """Archive or permanently delete a product.

    Args:
        product_id: SKU or numeric id (as string).
        archive: If True, mark `active` False; otherwise remove the product record.

    Returns:
        A dict containing a `message` describing the outcome.

    Raises:
        HTTPException(404): If the product is not found.

    Side effects:
        Mutates `data/products.json`.
    """

    return await products_service.delete_or_archive_product(product_id, archive)
