from fastapi import APIRouter
from app.api.v1 import user, test, auth

router = APIRouter()
router.include_router(router=test.router, prefix="/test", tags=["test"])
router.include_router(router=user.router, prefix="/user", tags=["user"])
router.include_router(router=auth.router, prefix="/auth", tags=["auth"])
