"""Генератор паролей и passphrase."""

import secrets
import string


# Словарь для генерации passphrase (английские слова)
WORDS = [
    "apple", "banana", "cherry", "dragon", "eagle", "forest", "garden", "hammer",
    "island", "jungle", "knight", "lighthouse", "mountain", "nature", "ocean",
    "planet", "quasar", "river", "sunset", "tiger", "universe", "valley",
    "waterfall", "xenon", "yacht", "zebra", "anchor", "bridge", "castle",
    "diamond", "elephant", "falcon", "galaxy", "horizon", "iceberg", "jewel",
    "kingdom", "lantern", "meadow", "nebula", "orchard", "palace", "quartz",
    "rainbow", "sapphire", "temple", "umbrella", "vortex", "wizard", "xylophone",
    "yonder", "zenith", "alpine", "breeze", "cascade", "dolphin", "echo",
    "flame", "glacier", "harbor", "infinity", "journey", "kayak", "lagoon",
    "mirage", "nimbus", "oasis", "pinnacle", "quiver", "relic", "summit",
    "tundra", "utopia", "vista", "whisper", "xenial", "yearn", "zephyr"
]


def generate_password(
    length: int = 16,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
    exclude_similar: bool = True,
) -> str:
    """
    Генерирует случайный пароль.
    
    Args:
        length: Длина пароля
        include_uppercase: Включать заглавные буквы
        include_lowercase: Включать строчные буквы
        include_digits: Включать цифры
        include_symbols: Включать символы
        exclude_similar: Исключать похожие символы (i, l, 1, L, o, 0, O)
    
    Returns:
        Сгенерированный пароль
    
    Raises:
        ValueError: Если не выбрано ни одного типа символов или длина слишком мала
    """
    if length < 4:
        raise ValueError("Длина пароля должна быть не менее 4 символов")
    
    # Формируем алфавит
    alphabet = ""
    
    if include_uppercase:
        if exclude_similar:
            alphabet += "ABCDEFGHJKLMNPQRSTUVWXYZ"  # Исключаем I, O
        else:
            alphabet += string.ascii_uppercase
    
    if include_lowercase:
        if exclude_similar:
            alphabet += "abcdefghijkmnopqrstuvwxyz"  # Исключаем l, o
        else:
            alphabet += string.ascii_lowercase
    
    if include_digits:
        if exclude_similar:
            alphabet += "23456789"  # Исключаем 0, 1
        else:
            alphabet += string.digits
    
    if include_symbols:
        alphabet += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    if not alphabet:
        raise ValueError("Необходимо выбрать хотя бы один тип символов")
    
    # Генерируем пароль
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    
    return password


def generate_passphrase(word_count: int = 4, separator: str = "-") -> str:
    """
    Генерирует passphrase из случайных слов.
    
    Args:
        word_count: Количество слов
        separator: Разделитель между словами
    
    Returns:
        Сгенерированная passphrase
    
    Raises:
        ValueError: Если количество слов меньше 3
    """
    if word_count < 3:
        raise ValueError("Количество слов должно быть не менее 3")
    
    words = [secrets.choice(WORDS) for _ in range(word_count)]
    return separator.join(words)

