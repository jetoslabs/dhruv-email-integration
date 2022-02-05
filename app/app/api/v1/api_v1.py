from fastapi import APIRouter
from app.api.v1 import users, test, auth, mail

router = APIRouter()
router.include_router(router=test.router, prefix="/test", tags=["test"])
router.include_router(router=users.router, prefix="/users", tags=["users"])
router.include_router(router=auth.router, prefix="/auth", tags=["auth"])
router.include_router(router=mail.router, prefix="/mail", tags=["mail"])
