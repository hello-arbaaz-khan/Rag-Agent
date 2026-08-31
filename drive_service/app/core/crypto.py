from cryptography.fernet import Fernet

from app.config import settings

_fernet = Fernet(settings.fernet_key)


def encrypt_token(plain_text: str, key_version: int = 1) -> str:
    return _fernet.encrypt(plain_text.encode()).decode()


def decrypt_token(encrypted_text: str, key_version: int = 1) -> str:
    return _fernet.decrypt(encrypted_text.encode()).decode()