from fastapi import APIRouter

from app.api.endpoints import admin, engagement, profile, properties, public

router = APIRouter()
router.include_router(public.router)
router.include_router(properties.router)
router.include_router(profile.router)
router.include_router(engagement.router)
router.include_router(admin.router)
