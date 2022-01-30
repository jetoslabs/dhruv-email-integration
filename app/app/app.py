from typing import Optional
from O365 import Account, FileSystemTokenBackend
from fastapi import FastAPI

app = FastAPI()

credentials = ('ee711872-3b83-46a4-a681-aff01ff4bdab','Utq7Q~i5IHQCyONc2uHIg-ZhNZSAlZ~k54rI9')
token_backend = FileSystemTokenBackend(token_path='my_folder', token_filename='my_token.txt')

account = Account(credentials, token_backend=token_backend)
@app.get("/")
def read_root():
    if account.authenticate(scopes=['mailbox','mailbox_shared','address_book','address_book']):
        return {"Authenticated !"}
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}


