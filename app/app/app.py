from typing import Optional
from O365 import Account, FileSystemTokenBackend
from fastapi import FastAPI

app = FastAPI()


@app.get("/authenticate")
def read_root(client_id: str, client_secert: str):
    # credentials = ('ee711872-3b83-46a4-a681-aff01ff4bdab', 'Utq7Q~i5IHQCyONc2uHIg-ZhNZSAlZ~k54rI9')
    credentials = (client_id, client_secert)
    token_backend = FileSystemTokenBackend(token_path='my_folder', token_filename='my_token.txt')
    account = Account(credentials, token_backend=token_backend)
    if account.authenticate(scopes=['mailbox', 'mailbox_shared', 'address_book', 'address_book']):
        return {"Authenticated !"}
    return {"Hello": "World"}


@app.get("/mails/read")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}
