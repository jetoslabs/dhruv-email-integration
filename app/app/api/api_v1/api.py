from fastapi import APIRouter
from app.api.api_v1.endpoints import test, auth, mails, users

router = APIRouter()

router.include_router(router=auth.router, prefix="/auth", tags=["auth"])

router.include_router(router=users.router, prefix="", tags=["users"])
router.include_router(router=mails.router, prefix="", tags=["mails"])

router.include_router(router=test.router, prefix="/test", tags=["test"])
