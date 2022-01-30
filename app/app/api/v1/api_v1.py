from fastapi import APIRouter
from app.api.v1 import mail, auth

v1_router = APIRouter()
v1_router.include_router(router=mail.router, prefix="/mail", tags=["mail"])
v1_router.include_router(router=auth.router, prefix="/auth", tags=["auth"])
