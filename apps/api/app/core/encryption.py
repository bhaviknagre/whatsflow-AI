from cryptography.fernet import Fernet

from app.core.config import settings


class TokenEncryption:
    def __init__(self) -> None:
        self._fernet = Fernet(
            settings.ENCRYPTION_KEY
        )

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(
            value.encode()
        ).decode()

    def decrypt(self, value: str) -> str:
        return self._fernet.decrypt(
            value.encode()
        ).decode()


token_encryption = TokenEncryption()