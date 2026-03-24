"""Валидация и оценка силы мастер-пароля."""

import re
import math
from typing import Tuple


# Список слабых паролей (топ-100)
COMMON_PASSWORDS = {
    "password", "123456", "123456789", "12345678", "12345", "1234567",
    "1234567890", "qwerty", "abc123", "password1", "123123", "admin",
    "letmein", "welcome", "monkey", "123456789", "1234567890", "qwerty123",
    "password123", "admin123", "root", "toor", "pass", "test", "guest",
    "user", "login", "welcome123", "master", "hello", "sunshine", "princess",
    "football", "baseball", "basketball", "superman", "batman", "trustno1",
    "dragon", "shadow", "michael", "jennifer", "jordan", "hunter", "joshua",
    "michelle", "charlie", "andrew", "matthew", "jessica", "samantha",
    "ashley", "amanda", "daniel", "christopher", "joseph", "david", "james",
    "robert", "john", "william", "richard", "thomas", "charles", "joseph",
    "christopher", "daniel", "matthew", "anthony", "mark", "donald", "steven",
    "paul", "andrew", "joshua", "kenneth", "kevin", "brian", "george",
    "timothy", "ronald", "jason", "edward", "jeffrey", "ryan", "jacob",
    "gary", "nicholas", "eric", "jonathan", "stephen", "larry", "justin",
    "scott", "brandon", "benjamin", "samuel", "frank", "gregory", "raymond",
    "alexander", "patrick", "jack", "dennis", "jerry", "tyler", "aaron",
}


def estimate_entropy(password: str) -> float:
    """
    Оценивает энтропию пароля в битах.
    
    Args:
        password: Пароль для оценки
    
    Returns:
        Энтропия в битах
    """
    if not password:
        return 0.0
    
    # Определяем размер алфавита
    has_lower = bool(re.search(r"[a-z]", password))
    has_upper = bool(re.search(r"[A-Z]", password))
    has_digits = bool(re.search(r"\d", password))
    has_symbols = bool(re.search(r"[^a-zA-Z0-9]", password))
    
    alphabet_size = 0
    if has_lower:
        alphabet_size += 26
    if has_upper:
        alphabet_size += 26
    if has_digits:
        alphabet_size += 10
    if has_symbols:
        alphabet_size += 32  # Примерно
    
    if alphabet_size == 0:
        return 0.0
    
    # Энтропия = log2(алфавит^длина)
    entropy = len(password) * math.log2(alphabet_size)
    
    return entropy


def validate_master_password(password: str) -> Tuple[bool, str]:
    """
    Валидирует мастер-пароль.
    
    Args:
        password: Пароль для валидации
    
    Returns:
        Кортеж (валиден, сообщение)
    """
    if not password:
        return False, "Пароль не может быть пустым"
    
    if len(password) < 8:
        return False, "Пароль должен содержать не менее 8 символов"
    
    # Проверка на слабые пароли
    if password.lower() in COMMON_PASSWORDS:
        return False, "Этот пароль слишком распространён. Выберите более уникальный."
    
    # Проверка энтропии
    entropy = estimate_entropy(password)
    if entropy < 40:
        return (
            False,
            f"Пароль слишком слабый (энтропия: {entropy:.1f} бит). "
            "Рекомендуется использовать пароль с энтропией не менее 40 бит.",
        )
    
    # Проверка разнообразия символов
    has_lower = bool(re.search(r"[a-z]", password))
    has_upper = bool(re.search(r"[A-Z]", password))
    has_digits = bool(re.search(r"\d", password))
    has_symbols = bool(re.search(r"[^a-zA-Z0-9]", password))
    
    char_types = sum([has_lower, has_upper, has_digits, has_symbols])
    if char_types < 2:
        return (
            False,
            "Пароль должен содержать символы хотя бы двух типов "
            "(заглавные, строчные, цифры, символы).",
        )
    
    # Проверка на повторяющиеся символы
    if len(set(password)) < len(password) * 0.5:
        return (
            False,
            "Пароль содержит слишком много повторяющихся символов.",
        )
    
    return True, "Пароль соответствует требованиям безопасности"

