"""Формат файла хранилища паролей."""

import struct
from dataclasses import dataclass
from typing import Optional
from .kdf import derive_key, DEFAULT_KDF_PARAMS
from .encryption import (
    generate_dek,
    generate_nonce,
    wrap_dek,
    unwrap_dek,
    encrypt_data,
    decrypt_data,
)

# Magic bytes для идентификации формата файла
MAGIC_BYTES = b"BRNGVLT1"
FORMAT_VERSION = 1
KDF_TYPE_ARGON2ID = 1


@dataclass
class VaultHeader:
    """Заголовок файла хранилища."""
    
    format_version: int
    kdf_type: int
    kdf_memory_cost: int
    kdf_time_cost: int
    kdf_parallelism: int
    salt: bytes
    dek_nonce: bytes
    wrapped_dek: bytes
    encrypted_payload_length: int


def serialize_header(header: VaultHeader) -> bytes:
    """
    Сериализует заголовок хранилища в бинарный формат.
    
    Формат:
    - Magic bytes: 8 байт
    - Format version: uint16 (2 байта)
    - KDF type: uint8 (1 байт)
    - KDF memory_cost: uint32 (4 байта)
    - KDF time_cost: uint32 (4 байта)
    - KDF parallelism: uint8 (1 байт)
    - Salt: 32 байта
    - DEK nonce: 12 байт
    - Wrapped DEK length: uint16 (2 байта)
    - Wrapped DEK: переменная длина
    - Encrypted payload length: uint32 (4 байта)
    
    Args:
        header: Заголовок для сериализации
    
    Returns:
        Сериализованный заголовок
    """
    parts = [
        MAGIC_BYTES,
        struct.pack(">H", header.format_version),  # uint16, big-endian
        struct.pack(">B", header.kdf_type),  # uint8
        struct.pack(">I", header.kdf_memory_cost),  # uint32
        struct.pack(">I", header.kdf_time_cost),  # uint32
        struct.pack(">B", header.kdf_parallelism),  # uint8
        header.salt,  # 32 байта
        header.dek_nonce,  # 12 байт
        struct.pack(">H", len(header.wrapped_dek)),  # uint16
        header.wrapped_dek,
        struct.pack(">I", header.encrypted_payload_length),  # uint32
    ]
    return b"".join(parts)


def deserialize_header(data: bytes) -> tuple[VaultHeader, int]:
    """
    Десериализует заголовок из бинарных данных.
    
    Args:
        data: Бинарные данные файла
    
    Returns:
        Кортеж (VaultHeader, offset) где offset - позиция начала payload
    
    Raises:
        ValueError: Если формат файла неверный
    """
    if len(data) < len(MAGIC_BYTES):
        raise ValueError("Файл слишком короткий")
    
    # Проверка magic bytes
    magic = data[:8]
    if magic != MAGIC_BYTES:
        raise ValueError(f"Неверный формат файла. Ожидался magic: {MAGIC_BYTES}, получен: {magic}")
    
    offset = 8
    
    # Format version
    format_version = struct.unpack(">H", data[offset : offset + 2])[0]
    offset += 2
    
    # KDF type
    kdf_type = struct.unpack(">B", data[offset : offset + 1])[0]
    offset += 1
    
    # KDF params
    kdf_memory_cost = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4
    kdf_time_cost = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4
    kdf_parallelism = struct.unpack(">B", data[offset : offset + 1])[0]
    offset += 1
    
    # Salt (32 байта)
    salt = data[offset : offset + 32]
    offset += 32
    
    # DEK nonce (12 байт)
    dek_nonce = data[offset : offset + 12]
    offset += 12
    
    # Wrapped DEK length
    wrapped_dek_length = struct.unpack(">H", data[offset : offset + 2])[0]
    offset += 2
    
    # Wrapped DEK
    wrapped_dek = data[offset : offset + wrapped_dek_length]
    offset += wrapped_dek_length
    
    # Encrypted payload length
    encrypted_payload_length = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4
    
    header = VaultHeader(
        format_version=format_version,
        kdf_type=kdf_type,
        kdf_memory_cost=kdf_memory_cost,
        kdf_time_cost=kdf_time_cost,
        kdf_parallelism=kdf_parallelism,
        salt=salt,
        dek_nonce=dek_nonce,
        wrapped_dek=wrapped_dek,
        encrypted_payload_length=encrypted_payload_length,
    )
    
    return header, offset


class VaultFormat:
    """Класс для работы с форматом файла хранилища."""
    
    @staticmethod
    def create_vault(master_password: str, payload_data: bytes, kdf_params: Optional[dict] = None) -> bytes:
        """
        Создаёт новый файл хранилища.
        
        Args:
            master_password: Мастер-пароль
            payload_data: Данные для шифрования (JSON в bytes)
            kdf_params: Параметры KDF (опционально)
        
        Returns:
            Полный файл хранилища в бинарном формате
        """
        if kdf_params is None:
            kdf_params = DEFAULT_KDF_PARAMS.copy()
        
        # Генерируем соль
        import os
        salt = os.urandom(32)
        
        # Выводим KEK из мастер-пароля
        kek = derive_key(master_password, salt, kdf_params)
        
        # Генерируем DEK
        dek = generate_dek()
        
        # Обёртываем DEK
        dek_nonce = generate_nonce()
        wrapped_dek = wrap_dek(dek, kek, dek_nonce)
        
        # Шифруем payload
        ciphertext, payload_nonce = encrypt_data(payload_data, dek)
        
        # Создаём заголовок
        header = VaultHeader(
            format_version=FORMAT_VERSION,
            kdf_type=KDF_TYPE_ARGON2ID,
            kdf_memory_cost=kdf_params["memory_cost"],
            kdf_time_cost=kdf_params["time_cost"],
            kdf_parallelism=kdf_params["parallelism"],
            salt=salt,
            dek_nonce=dek_nonce,
            wrapped_dek=wrapped_dek,
            encrypted_payload_length=len(ciphertext) + len(payload_nonce),  # ciphertext включает nonce в начале
        )
        
        # Сериализуем заголовок
        header_bytes = serialize_header(header)
        
        # Объединяем: заголовок + nonce + ciphertext
        # В AES-GCM nonce обычно передаётся отдельно, но для упрощения
        # мы храним его вместе с ciphertext
        full_payload = payload_nonce + ciphertext
        
        return header_bytes + full_payload
    
    @staticmethod
    def load_vault(file_data: bytes, master_password: str) -> bytes:
        """
        Загружает и расшифровывает хранилище.
        
        Args:
            file_data: Полный файл хранилища
            master_password: Мастер-пароль
        
        Returns:
            Расшифрованные данные payload
        
        Raises:
            ValueError: Если формат неверный или пароль неверный
        """
        # Десериализуем заголовок
        header, offset = deserialize_header(file_data)
        
        # Проверяем версию формата
        if header.format_version != FORMAT_VERSION:
            raise ValueError(f"Неподдерживаемая версия формата: {header.format_version}")
        
        # Проверяем тип KDF
        if header.kdf_type != KDF_TYPE_ARGON2ID:
            raise ValueError(f"Неподдерживаемый тип KDF: {header.kdf_type}")
        
        # Выводим KEK
        kdf_params = {
            "memory_cost": header.kdf_memory_cost,
            "time_cost": header.kdf_time_cost,
            "parallelism": header.kdf_parallelism,
        }
        kek = derive_key(master_password, header.salt, kdf_params)
        
        # Развёртываем DEK
        dek = unwrap_dek(header.wrapped_dek, kek, header.dek_nonce)
        
        # Извлекаем зашифрованный payload
        if offset + header.encrypted_payload_length > len(file_data):
            raise ValueError("Файл повреждён: неверная длина payload")
        
        encrypted_payload = file_data[offset : offset + header.encrypted_payload_length]
        
        # Nonce для payload (первые 12 байт)
        payload_nonce = encrypted_payload[:12]
        ciphertext = encrypted_payload[12:]
        
        # Расшифровываем payload
        payload_data = decrypt_data(ciphertext, payload_nonce, dek)
        
        return payload_data

