"""Управление файлом хранилища паролей."""

import json
import os
from typing import Optional
from ..crypto.vault_format import VaultFormat
from ..models.vault import Vault


class VaultManager:
    """Менеджер для работы с файлом хранилища."""
    
    def __init__(self, filepath: str):
        """
        Инициализирует менеджер хранилища.
        
        Args:
            filepath: Путь к файлу хранилища
        """
        self.filepath = filepath
        self._is_locked = True
        self._master_password: Optional[str] = None
    
    @property
    def is_locked(self) -> bool:
        """Проверяет, заблокировано ли хранилище."""
        return self._is_locked
    
    def lock(self) -> None:
        """Блокирует хранилище, очищая мастер-пароль из памяти."""
        self._is_locked = True
        self._master_password = None
    
    def unlock(self, master_password: str) -> None:
        """
        Разблокирует хранилище.
        
        Args:
            master_password: Мастер-пароль
        """
        self._master_password = master_password
        self._is_locked = False
    
    @classmethod
    def create_vault(cls, filepath: str, master_password: str) -> "VaultManager":
        """
        Создаёт новое хранилище.
        
        Args:
            filepath: Путь к файлу хранилища
            master_password: Мастер-пароль
        
        Returns:
            VaultManager для нового хранилища
        
        Raises:
            FileExistsError: Если файл уже существует
        """
        if os.path.exists(filepath):
            raise FileExistsError(f"Файл {filepath} уже существует")
        
        # Создаём пустое хранилище
        vault = Vault()
        
        # Сохраняем его
        manager = cls(filepath)
        manager.save_vault(vault, master_password)
        manager.unlock(master_password)
        
        return manager
    
    def load_vault(self, master_password: str) -> Vault:
        """
        Загружает хранилище из файла.
        
        Args:
            master_password: Мастер-пароль
        
        Returns:
            Загруженное хранилище
        
        Raises:
            FileNotFoundError: Если файл не существует
            ValueError: Если пароль неверный или файл повреждён
        """
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Файл {self.filepath} не найден")
        
        # Читаем файл
        with open(self.filepath, "rb") as f:
            file_data = f.read()
        
        # Расшифровываем
        try:
            payload_data = VaultFormat.load_vault(file_data, master_password)
        except ValueError as e:
            raise ValueError(f"Не удалось загрузить хранилище: {e}") from e
        
        # Десериализуем JSON
        try:
            vault_dict = json.loads(payload_data.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Неверный формат данных в хранилище: {e}") from e
        
        # Создаём объект хранилища
        vault = Vault.from_dict(vault_dict)
        
        # Разблокируем менеджер
        self.unlock(master_password)
        
        return vault
    
    def save_vault(self, vault: Vault, master_password: Optional[str] = None) -> None:
        """
        Сохраняет хранилище в файл.
        
        Args:
            vault: Хранилище для сохранения
            master_password: Мастер-пароль (если не указан, используется текущий)
        
        Raises:
            ValueError: Если хранилище заблокировано и пароль не указан
        """
        password = master_password if master_password is not None else self._master_password
        
        if password is None:
            raise ValueError("Хранилище заблокировано. Укажите мастер-пароль.")
        
        # Сериализуем в JSON
        vault_dict = vault.to_dict()
        payload_data = json.dumps(vault_dict, ensure_ascii=False, indent=2).encode("utf-8")
        
        # Шифруем и создаём файл
        file_data = VaultFormat.create_vault(password, payload_data)
        
        # Сохраняем в файл
        # Используем временный файл для атомарности записи
        temp_filepath = self.filepath + ".tmp"
        with open(temp_filepath, "wb") as f:
            f.write(file_data)
        
        # Атомарно заменяем старый файл новым
        if os.path.exists(self.filepath):
            os.replace(temp_filepath, self.filepath)
        else:
            os.rename(temp_filepath, self.filepath)
        
        # Обновляем мастер-пароль в менеджере, если он был изменён
        if master_password is not None:
            self.unlock(master_password)
    
    def change_master_password(
        self, old_password: str, new_password: str
    ) -> None:
        """
        Меняет мастер-пароль хранилища.
        
        Это перешифровывает хранилище с новым паролем.
        
        Args:
            old_password: Старый мастер-пароль
            new_password: Новый мастер-пароль
        
        Raises:
            ValueError: Если старый пароль неверный
        """
        # Загружаем хранилище со старым паролем
        try:
            vault = self.load_vault(old_password)
        except ValueError as e:
            raise ValueError(f"Неверный старый пароль: {e}") from e
        
        # Сохраняем с новым паролем
        self.save_vault(vault, new_password)

