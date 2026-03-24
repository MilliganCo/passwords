"""Тесты для криптографических модулей."""

import unittest
import os
import json
from src.crypto.kdf import derive_key, hkdf_expand, DEFAULT_KDF_PARAMS
from src.crypto.encryption import (
    generate_dek,
    generate_nonce,
    wrap_dek,
    unwrap_dek,
    encrypt_data,
    decrypt_data,
)
from src.crypto.vault_format import (
    VaultFormat,
    VaultHeader,
    serialize_header,
    deserialize_header,
    MAGIC_BYTES,
    FORMAT_VERSION,
)


class TestKDF(unittest.TestCase):
    """Тесты для KDF."""
    
    def test_derive_key(self):
        """Тест вывода ключа из пароля."""
        password = "test_password_123"
        salt = os.urandom(32)
        
        key = derive_key(password, salt)
        
        self.assertEqual(len(key), 32)
        self.assertIsInstance(key, bytes)
    
    def test_derive_key_deterministic(self):
        """Тест детерминированности вывода ключа."""
        password = "test_password"
        salt = os.urandom(32)
        
        key1 = derive_key(password, salt)
        key2 = derive_key(password, salt)
        
        self.assertEqual(key1, key2)
    
    def test_derive_key_different_salts(self):
        """Тест, что разные соли дают разные ключи."""
        password = "test_password"
        salt1 = os.urandom(32)
        salt2 = os.urandom(32)
        
        key1 = derive_key(password, salt1)
        key2 = derive_key(password, salt2)
        
        self.assertNotEqual(key1, key2)
    
    def test_derive_key_custom_params(self):
        """Тест вывода ключа с пользовательскими параметрами."""
        password = "test_password"
        salt = os.urandom(32)
        params = {"memory_cost": 32768, "time_cost": 2, "parallelism": 2}
        
        key = derive_key(password, salt, params)
        
        self.assertEqual(len(key), 32)
    
    def test_hkdf_expand(self):
        """Тест расширения ключа через HKDF."""
        key = os.urandom(32)
        info = b"test_info"
        
        expanded = hkdf_expand(key, info, 32)
        
        self.assertEqual(len(expanded), 32)
        self.assertIsInstance(expanded, bytes)
    
    def test_hkdf_expand_different_info(self):
        """Тест, что разные info дают разные ключи."""
        key = os.urandom(32)
        
        expanded1 = hkdf_expand(key, b"info1", 32)
        expanded2 = hkdf_expand(key, b"info2", 32)
        
        self.assertNotEqual(expanded1, expanded2)


class TestEncryption(unittest.TestCase):
    """Тесты для шифрования."""
    
    def test_generate_dek(self):
        """Тест генерации DEK."""
        dek = generate_dek()
        
        self.assertEqual(len(dek), 32)
        self.assertIsInstance(dek, bytes)
    
    def test_generate_dek_unique(self):
        """Тест, что генерируются уникальные DEK."""
        dek1 = generate_dek()
        dek2 = generate_dek()
        
        self.assertNotEqual(dek1, dek2)
    
    def test_generate_nonce(self):
        """Тест генерации nonce."""
        nonce = generate_nonce()
        
        self.assertEqual(len(nonce), 12)
        self.assertIsInstance(nonce, bytes)
    
    def test_wrap_unwrap_dek(self):
        """Тест обёртывания и развёртывания DEK."""
        dek = generate_dek()
        kek = os.urandom(32)
        nonce = generate_nonce()
        
        wrapped = wrap_dek(dek, kek, nonce)
        unwrapped = unwrap_dek(wrapped, kek, nonce)
        
        self.assertEqual(dek, unwrapped)
    
    def test_wrap_unwrap_dek_wrong_key(self):
        """Тест, что неправильный ключ не развёртывает DEK."""
        dek = generate_dek()
        kek1 = os.urandom(32)
        kek2 = os.urandom(32)
        nonce = generate_nonce()
        
        wrapped = wrap_dek(dek, kek1, nonce)
        
        with self.assertRaises(ValueError):
            unwrap_dek(wrapped, kek2, nonce)
    
    def test_encrypt_decrypt_data(self):
        """Тест шифрования и расшифровки данных."""
        data = b"test data for encryption"
        dek = generate_dek()
        
        ciphertext, nonce = encrypt_data(data, dek)
        decrypted = decrypt_data(ciphertext, nonce, dek)
        
        self.assertEqual(data, decrypted)
        self.assertNotEqual(data, ciphertext)
    
    def test_encrypt_decrypt_data_wrong_key(self):
        """Тест, что неправильный ключ не расшифровывает данные."""
        data = b"test data"
        dek1 = generate_dek()
        dek2 = generate_dek()
        
        ciphertext, nonce = encrypt_data(data, dek1)
        
        with self.assertRaises(ValueError):
            decrypt_data(ciphertext, nonce, dek2)
    
    def test_encrypt_decrypt_empty_data(self):
        """Тест шифрования пустых данных."""
        data = b""
        dek = generate_dek()
        
        ciphertext, nonce = encrypt_data(data, dek)
        decrypted = decrypt_data(ciphertext, nonce, dek)
        
        self.assertEqual(data, decrypted)
    
    def test_encrypt_decrypt_large_data(self):
        """Тест шифрования больших данных."""
        data = b"x" * 10000
        dek = generate_dek()
        
        ciphertext, nonce = encrypt_data(data, dek)
        decrypted = decrypt_data(ciphertext, nonce, dek)
        
        self.assertEqual(data, decrypted)


class TestVaultFormat(unittest.TestCase):
    """Тесты для формата файла хранилища."""
    
    def test_serialize_deserialize_header(self):
        """Тест сериализации и десериализации заголовка."""
        header = VaultHeader(
            format_version=FORMAT_VERSION,
            kdf_type=1,
            kdf_memory_cost=65536,
            kdf_time_cost=3,
            kdf_parallelism=4,
            salt=os.urandom(32),
            dek_nonce=os.urandom(12),
            wrapped_dek=os.urandom(48),
            encrypted_payload_length=1000,
        )
        
        serialized = serialize_header(header)
        deserialized, offset = deserialize_header(serialized)
        
        self.assertEqual(header.format_version, deserialized.format_version)
        self.assertEqual(header.kdf_type, deserialized.kdf_type)
        self.assertEqual(header.kdf_memory_cost, deserialized.kdf_memory_cost)
        self.assertEqual(header.kdf_time_cost, deserialized.kdf_time_cost)
        self.assertEqual(header.kdf_parallelism, deserialized.kdf_parallelism)
        self.assertEqual(header.salt, deserialized.salt)
        self.assertEqual(header.dek_nonce, deserialized.dek_nonce)
        self.assertEqual(header.wrapped_dek, deserialized.wrapped_dek)
        self.assertEqual(header.encrypted_payload_length, deserialized.encrypted_payload_length)
    
    def test_deserialize_header_invalid_magic(self):
        """Тест десериализации с неверным magic."""
        invalid_data = b"INVALID" + b"x" * 100
        
        with self.assertRaises(ValueError):
            deserialize_header(invalid_data)
    
    def test_create_load_vault(self):
        """Тест создания и загрузки хранилища."""
        master_password = "test_master_password_123"
        payload_data = json.dumps({"test": "data"}).encode("utf-8")
        
        # Создаём хранилище
        vault_data = VaultFormat.create_vault(master_password, payload_data)
        
        # Проверяем magic bytes
        self.assertEqual(vault_data[:8], MAGIC_BYTES)
        
        # Загружаем хранилище
        decrypted_payload = VaultFormat.load_vault(vault_data, master_password)
        
        self.assertEqual(payload_data, decrypted_payload)
    
    def test_create_load_vault_wrong_password(self):
        """Тест, что неправильный пароль не загружает хранилище."""
        master_password = "correct_password"
        wrong_password = "wrong_password"
        payload_data = json.dumps({"test": "data"}).encode("utf-8")
        
        vault_data = VaultFormat.create_vault(master_password, payload_data)
        
        with self.assertRaises(ValueError):
            VaultFormat.load_vault(vault_data, wrong_password)
    
    def test_create_load_vault_different_passwords(self):
        """Тест создания хранилищ с разными паролями."""
        password1 = "password1"
        password2 = "password2"
        payload_data = json.dumps({"test": "data"}).encode("utf-8")
        
        vault1 = VaultFormat.create_vault(password1, payload_data)
        vault2 = VaultFormat.create_vault(password2, payload_data)
        
        # Хранилища должны быть разными
        self.assertNotEqual(vault1, vault2)
        
        # Каждое хранилище должно открываться своим паролем
        decrypted1 = VaultFormat.load_vault(vault1, password1)
        decrypted2 = VaultFormat.load_vault(vault2, password2)
        
        self.assertEqual(decrypted1, payload_data)
        self.assertEqual(decrypted2, payload_data)
    
    def test_create_load_vault_large_payload(self):
        """Тест создания и загрузки хранилища с большим payload."""
        master_password = "test_password"
        large_payload = json.dumps({"data": "x" * 10000}).encode("utf-8")
        
        vault_data = VaultFormat.create_vault(master_password, large_payload)
        decrypted_payload = VaultFormat.load_vault(vault_data, master_password)
        
        self.assertEqual(large_payload, decrypted_payload)


if __name__ == "__main__":
    unittest.main()

