"""KDF (Key Derivation Functions) для менеджера паролей."""

from typing import Dict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from argon2 import low_level
import argon2

# Параметры Argon2id по умолчанию
DEFAULT_KDF_PARAMS = {
    "memory_cost": 65536,  # 64 MB
    "time_cost": 3,
    "parallelism": 4,
}


def derive_key(password: str, salt: bytes, params: Dict = None) -> bytes:
    """
    Выводит ключ из мастер-пароля используя Argon2id KDF.
    
    Args:
        password: Мастер-пароль
        salt: Случайная соль (32 байта)
        params: Параметры KDF (memory_cost, time_cost, parallelism)
    
    Returns:
        Выведенный ключ (32 байта)
    """
    if params is None:
        params = DEFAULT_KDF_PARAMS.copy()
    
    # Используем низкоуровневый API Argon2id для прямого получения ключа
    key = low_level.hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=params["time_cost"],
        memory_cost=params["memory_cost"],
        parallelism=params["parallelism"],
        hash_len=32,
        type=argon2.Type.ID,
    )
    
    return key


def hkdf_expand(key: bytes, info: bytes, length: int = 32) -> bytes:
    """
    Расширяет ключ используя HKDF для получения дополнительных ключей.
    
    Args:
        key: Входной ключ
        info: Контекстная информация (application-specific)
        length: Длина выходного ключа в байтах
    
    Returns:
        Расширенный ключ
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
        backend=default_backend(),
    )
    return hkdf.derive(key)

