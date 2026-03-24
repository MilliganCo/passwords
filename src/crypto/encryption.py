"""Шифрование данных для менеджера паролей."""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


def generate_dek() -> bytes:
    """
    Генерирует случайный DEK (Data Encryption Key).
    
    Returns:
        Случайный ключ длиной 32 байта (256 бит)
    """
    return os.urandom(32)


def generate_nonce() -> bytes:
    """
    Генерирует случайный nonce для AES-GCM.
    
    Returns:
        Случайный nonce длиной 12 байт (96 бит)
    """
    return os.urandom(12)


def wrap_dek(dek: bytes, kek: bytes, nonce: bytes) -> bytes:
    """
    Обёртывает DEK используя KEK (Key Encryption Key) с AES-256-GCM.
    
    Args:
        dek: Data Encryption Key для обёртывания
        kek: Key Encryption Key
        nonce: Nonce для шифрования (12 байт)
    
    Returns:
        Зашифрованный DEK с тегом аутентификации
    """
    aesgcm = AESGCM(kek)
    wrapped = aesgcm.encrypt(nonce, dek, None)
    return wrapped


def unwrap_dek(wrapped_dek: bytes, kek: bytes, nonce: bytes) -> bytes:
    """
    Развёртывает DEK используя KEK.
    
    Args:
        wrapped_dek: Зашифрованный DEK с тегом
        kek: Key Encryption Key
        nonce: Nonce, использованный при шифровании
    
    Returns:
        Расшифрованный DEK
    
    Raises:
        ValueError: Если расшифровка не удалась (неверный ключ или повреждённые данные)
    """
    aesgcm = AESGCM(kek)
    try:
        dek = aesgcm.decrypt(nonce, wrapped_dek, None)
        return dek
    except Exception as e:
        raise ValueError("Не удалось расшифровать DEK. Возможно, неверный мастер-пароль.") from e


def encrypt_data(data: bytes, dek: bytes) -> tuple[bytes, bytes]:
    """
    Шифрует данные используя DEK с AES-256-GCM.
    
    Args:
        data: Данные для шифрования
        dek: Data Encryption Key
    
    Returns:
        Кортеж (ciphertext, nonce)
    """
    nonce = generate_nonce()
    aesgcm = AESGCM(dek)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return ciphertext, nonce


def decrypt_data(ciphertext: bytes, nonce: bytes, dek: bytes) -> bytes:
    """
    Расшифровывает данные используя DEK.
    
    Args:
        ciphertext: Зашифрованные данные с тегом
        nonce: Nonce, использованный при шифровании
        dek: Data Encryption Key
    
    Returns:
        Расшифрованные данные
    
    Raises:
        ValueError: Если расшифровка не удалась
    """
    aesgcm = AESGCM(dek)
    try:
        data = aesgcm.decrypt(nonce, ciphertext, None)
        return data
    except Exception as e:
        raise ValueError("Не удалось расшифровать данные. Возможно, файл повреждён.") from e

