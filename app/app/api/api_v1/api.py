from fastapi import APIRouter
from app.api.api_v1.endpoints import test, auth, mail, users

router = APIRouter()

router.include_router(router=auth.router, prefix="/auth", tags=["auth"])

router.include_router(router=users.router, prefix="/users", tags=["users"])
router.include_router(router=mail.router, prefix="/users", tags=["mail"])

router.include_router(router=test.router, prefix="/test", tags=["test"])
