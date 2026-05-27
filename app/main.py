from fastapi import FastAPI

from app.routers.customer import router as customers_router
from app.routers.products import router as products_router
from app.routers.sales import router as sales_router

app = FastAPI(title="Retail Outlet Backend")

app.include_router(customers_router)
app.include_router(products_router)
app.include_router(sales_router)


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
