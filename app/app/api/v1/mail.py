import time
from typing import Optional
from fastapi import APIRouter
# from app.api.deps import auth

router = APIRouter()


@router.get("/")
async def wait_late():
    time.sleep(30)
    return "done"

# globalAccount = auth('ee711872-3b83-46a4-a681-aff01ff4bdab', 'Utq7Q~i5IHQCyONc2uHIg-ZhNZSAlZ~k54rI9')


# @router.get("/read")
# def read_item(item_id: int, q: Optional[str] = None):
#     mailbox = globalAccount.mailbox()
#
#     inbox = mailbox.inbox_folder()
#     for message in inbox.get_messages():
#         print(message)
#
#     sent_folder = mailbox.sent_folder()
#     for message in sent_folder.get_messages():
#         print(message)
#
#     # new_messages = mailbox.get_messages(limit=100, query=None, order_by=None, batch=None, download_attachments=False)
#     # for message in new_messages:
#     #     print(message)
#
#     return {"item_id": item_id, "q": q}