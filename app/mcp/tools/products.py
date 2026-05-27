from typing import List, Optional

from app.mcp.server import mcp

from app.schemas.product import ProductOut, ProductCreate, ProductPut, ProductStockPatch
from app.services import products as products_service


@mcp.tool
async def list_products(category: Optional[str] = None, low_stock: bool = False) -> List[ProductOut]:
    return await products_service.list_products(category=category, low_stock=low_stock)


@mcp.tool
async def create_product(payload: ProductCreate) -> ProductOut:
    return await products_service.create_product(payload)


@mcp.tool
async def get_product(product_id: str) -> ProductOut:
    return await products_service.get_product(product_id)


@mcp.tool
async def update_product(product_id: str, payload: ProductPut) -> ProductOut:
    return await products_service.update_product(product_id, payload)


@mcp.tool
async def patch_product_stock(product_id: str, payload: ProductStockPatch) -> ProductOut:
    return await products_service.patch_product_stock(product_id, payload)


@mcp.tool
async def delete_or_archive_product(product_id: str, archive: bool = True) -> dict:
    return await products_service.delete_or_archive_product(product_id, archive)
