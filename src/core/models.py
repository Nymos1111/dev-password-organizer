from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import json
import os
from .encryption import PasswordEncryption


class DatabaseCredential:
    def __init__(self, name: str, host: str, user: str, password: str, port: int = 3306):
        self.name = name
        self.host = host
        self.user = user
        self.password = password
        self.port = port

    def to_dict(self) -> dict:
        return {
            "type": "database",  # ✅ ДОБАВЛЕНО: поле type, чтобы проверка при загрузке работала
            "name": self.name,
            "host": self.host,
            "user": self.user,
            "password": self.password,  # ✅ Сохраняем как 'password'
            "port": self.port,
        }

    def __str__(self):
        return f"[DB] {self.name} ({self.host}:{self.port})"


class Project:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.credentials: Dict[str, DatabaseCredential] = {}

    def add_credential(self, credential: DatabaseCredential):
        self.credentials[credential.name] = credential

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "credentials": {name: cred.to_dict() for name, cred in self.credentials.items()}
        }


class Vault:
    SALT_LENGTH = 16

    def __init__(self, master_password: str):
        self.projects: Dict[str, Project] = {}
        self.encryption = PasswordEncryption(master_password)

    def add_project(self, project: Project):
        self.projects[project.name] = project

    def list_projects(self) -> List[Project]:
        return list(self.projects.values())

    def save_to_file(self, filepath: str):
        # 1. Данные
        data = {
            "projects": {name: proj.to_dict() for name, proj in self.projects.items()},
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        # 2. Шифрование
        encrypted_data = self.encryption.encrypt(json_str)
        salt_bytes = self.encryption.get_salt()

        # 3. Запись: Данные + Соль в конце
        with open(filepath, "wb") as f:
            f.write(encrypted_data)
            f.write(salt_bytes)

    @classmethod
    def load_from_file(cls, filepath: str, master_password: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError("Файл Vault не найден.")

        try:
            with open(filepath, "rb") as f:
                full_data = f.read()

            if len(full_data) < cls.SALT_LENGTH:
                raise ValueError("Файл поврежден")

            # 1. Извлекаем соль (последние 16 байт)
            salt = full_data[-cls.SALT_LENGTH:]
            encrypted_data = full_data[:-cls.SALT_LENGTH]

            # 2. Дешифруем
            decryptor = PasswordEncryption.from_salt_and_password(master_password, salt)
            json_str = decryptor.decrypt(encrypted_data)
            data = json.loads(json_str)

            # 3. Восстанавливаем объекты
            vault = cls(master_password)

            # .get("projects", {}) защищает от ошибки, если проектов нет
            for proj_data in data.get("projects", {}).values():
                proj = Project(proj_data["name"], proj_data["description"])

                # ✅ ИСПРАВЛЕНИЕ: перебираем .values(), так как credentials - это словарь
                for cred_data in proj_data.get("credentials", {}).values():
                    if cred_data.get("type") == "database":
                        cred = DatabaseCredential(
                            name=cred_data["name"],
                            host=cred_data["host"],
                            user=cred_data["user"],
                            password=cred_data["password"],  # ✅ ИСПРАВЛЕНИЕ: читаем 'password', а не 'value'
                            port=cred_data["port"]
                        )
                        proj.add_credential(cred)
                vault.add_project(proj)
            return vault

        except Exception as e:
            # Чтобы видеть реальную ошибку при отладке, можно раскомментировать print(e)
            # print(f"DEBUG Error: {e}")
            raise ValueError("❌ Неверный мастер-пароль или повреждённый файл") from e