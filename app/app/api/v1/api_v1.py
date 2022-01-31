from fastapi import APIRouter
from app.api.v1 import mail, auth

router = APIRouter()
router.include_router(router=mail.router, prefix="/mail", tags=["mail"])
router.include_router(router=auth.router, prefix="/auth", tags=["auth"])
