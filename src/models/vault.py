"""Модель хранилища паролей."""

from typing import List, Optional
from datetime import datetime
from .password_entry import PasswordEntry


class Vault:
    """Хранилище паролей."""
    
    def __init__(self):
        """Инициализирует пустое хранилище."""
        self.entries: List[PasswordEntry] = []
        self.metadata = {
            "version": 1,
            "created_at": datetime.utcnow().isoformat(),
        }
    
    def add_entry(self, entry: PasswordEntry) -> None:
        """
        Добавляет запись в хранилище.
        
        Args:
            entry: Запись для добавления
        """
        # Проверяем, что запись с таким ID ещё не существует
        if any(e.id == entry.id for e in self.entries):
            raise ValueError(f"Запись с ID {entry.id} уже существует")
        self.entries.append(entry)
    
    def update_entry(self, entry_id: str, entry: PasswordEntry) -> None:
        """
        Обновляет запись в хранилище.
        
        Args:
            entry_id: ID записи для обновления
            entry: Обновлённая запись
        
        Raises:
            ValueError: Если запись не найдена
        """
        index = self._find_entry_index(entry_id)
        if index is None:
            raise ValueError(f"Запись с ID {entry_id} не найдена")
        
        # Сохраняем ID
        entry.id = entry_id
        self.entries[index] = entry
    
    def delete_entry(self, entry_id: str) -> None:
        """
        Удаляет запись из хранилища.
        
        Args:
            entry_id: ID записи для удаления
        
        Raises:
            ValueError: Если запись не найдена
        """
        index = self._find_entry_index(entry_id)
        if index is None:
            raise ValueError(f"Запись с ID {entry_id} не найдена")
        del self.entries[index]
    
    def get_entry(self, entry_id: str) -> Optional[PasswordEntry]:
        """
        Получает запись по ID.
        
        Args:
            entry_id: ID записи
        
        Returns:
            Запись или None, если не найдена
        """
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def search(self, query: str) -> List[PasswordEntry]:
        """
        Ищет записи по запросу.
        
        Поиск выполняется по title, username, url, notes, category и tags.
        
        Args:
            query: Поисковый запрос (регистронезависимый)
        
        Returns:
            Список найденных записей
        """
        query_lower = query.lower()
        results = []
        
        for entry in self.entries:
            # Поиск по различным полям
            if (
                query_lower in entry.title.lower()
                or query_lower in entry.username.lower()
                or query_lower in entry.url.lower()
                or query_lower in entry.notes.lower()
                or query_lower in entry.category.lower()
                or any(query_lower in tag.lower() for tag in entry.tags)
            ):
                results.append(entry)
        
        return results
    
    def get_by_category(self, category: str) -> List[PasswordEntry]:
        """
        Получает все записи из указанной категории.
        
        Args:
            category: Название категории
        
        Returns:
            Список записей в категории
        """
        return [entry for entry in self.entries if entry.category == category]
    
    def get_all_categories(self) -> List[str]:
        """
        Получает список всех категорий.
        
        Returns:
            Список уникальных категорий
        """
        categories = set(entry.category for entry in self.entries if entry.category)
        return sorted(list(categories))
    
    def get_all_tags(self) -> List[str]:
        """
        Получает список всех тегов.
        
        Returns:
            Список уникальных тегов
        """
        tags = set()
        for entry in self.entries:
            tags.update(entry.tags)
        return sorted(list(tags))
    
    def to_dict(self) -> dict:
        """Преобразует хранилище в словарь для сериализации."""
        return {
            "entries": [entry.to_dict() for entry in self.entries],
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Vault":
        """Создаёт хранилище из словаря."""
        vault = cls()
        vault.metadata = data.get("metadata", {"version": 1})
        
        entries_data = data.get("entries", [])
        for entry_data in entries_data:
            entry = PasswordEntry.from_dict(entry_data)
            vault.entries.append(entry)
        
        return vault
    
    def _find_entry_index(self, entry_id: str) -> Optional[int]:
        """Находит индекс записи по ID."""
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                return i
        return None

