"""
Compatibility wrapper for the canonical orders router.

The application registers app.routers.orders directly in main.py. This module is
kept only so older imports of app.routers.order do not reintroduce the previous
conflicting order workflow.
"""

from fastapi import APIRouter

from app.routers.orders import router as orders_router


router = APIRouter(prefix="/orders", tags=["Orders"])
router.include_router(orders_router)
