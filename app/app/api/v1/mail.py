from typing import Optional
from fastapi import APIRouter
from app.api.deps import auth

router = APIRouter()

globalAccount = auth('ee711872-3b83-46a4-a681-aff01ff4bdab', 'Utq7Q~i5IHQCyONc2uHIg-ZhNZSAlZ~k54rI9')


@router.get("/read")
def read_item(item_id: int, q: Optional[str] = None):
    mailbox = globalAccount.mailbox()

    inbox = mailbox.inbox_folder()

    for message in inbox.get_messages():
        print(message)

    sent_folder = mailbox.sent_folder()

    for message in sent_folder.get_messages():
        print(message)

    return {"item_id": item_id, "q": q}