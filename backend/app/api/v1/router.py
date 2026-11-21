from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.customers import router as customers_router
from app.api.v1.media import router as media_router
from app.api.v1.optimizations import router as optimizations_router
from app.api.v1.orders import router as orders_router
from app.api.v1.payments import router as payments_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(customers_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)
api_router.include_router(media_router)
api_router.include_router(optimizations_router)
api_router.include_router(analytics_router)
