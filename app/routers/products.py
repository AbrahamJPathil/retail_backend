from typing import List

from fastapi import APIRouter, Query

from app.schemas.product import ProductCreate, ProductOut, ProductPut, ProductStockPatch
from app.services import products as products_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[ProductOut])
async def list_products(
	category: str | None = Query(default=None),
	low_stock: bool = Query(default=False),
) -> List[ProductOut]:
	return await products_service.list_products(category=category, low_stock=low_stock)


@router.post("/", response_model=ProductOut, status_code=201)
async def create_product(payload: ProductCreate) -> ProductOut:
	return await products_service.create_product(payload)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: str) -> ProductOut:
	return await products_service.get_product(product_id)


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, payload: ProductPut) -> ProductOut:
	return await products_service.update_product(product_id, payload)


@router.patch("/{product_id}/stock", response_model=ProductOut)
async def patch_product_stock(product_id: str, payload: ProductStockPatch) -> ProductOut:
	return await products_service.patch_product_stock(product_id, payload)


@router.delete("/{product_id}")
async def delete_or_archive_product(
	product_id: str,
	archive: bool = Query(default=True),
) -> dict:
	return await products_service.delete_or_archive_product(product_id, archive)
