from O365 import Account, FileSystemTokenBackend


def auth(client_id: str, client_secert: str) -> Account:
    credentials = (client_id, client_secert)
    token_backend = FileSystemTokenBackend(token_path='my_folder', token_filename='my_token.txt')
    account = Account(credentials, token_backend=token_backend)
    print('Authenticated!')
    return account