"""Модуль криптографии для менеджера паролей."""

from .kdf import derive_key, hkdf_expand
from .encryption import generate_dek, wrap_dek, unwrap_dek, encrypt_data, decrypt_data
from .vault_format import VaultHeader, serialize_header, deserialize_header, VaultFormat

__all__ = [
    "derive_key",
    "hkdf_expand",
    "generate_dek",
    "wrap_dek",
    "unwrap_dek",
    "encrypt_data",
    "decrypt_data",
    "VaultHeader",
    "serialize_header",
    "deserialize_header",
    "VaultFormat",
]

