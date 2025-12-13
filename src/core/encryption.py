import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class PasswordEncryption:
    def __init__(self, master_password: str, salt: bytes = None):
        # Если соль не передана, генерируем новую (для сохранения)
        # Если передана — используем её (для загрузки)
        self.salt = salt if salt else os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        # Генерируем ключ из пароля и соли
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode('utf-8')))
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode('utf-8'))

    def decrypt(self, token: bytes) -> str:
        return self.cipher.decrypt(token).decode('utf-8')

    def get_salt(self) -> bytes:
        return self.salt

    @classmethod
    def from_salt_and_password(cls, master_password: str, salt: bytes):
        """Создаёт экземпляр для расшифровки с известной солью"""
        return cls(master_password, salt)