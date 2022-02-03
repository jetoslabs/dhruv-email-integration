import time
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def wait_late():
    time.sleep(30)
    return "done"
