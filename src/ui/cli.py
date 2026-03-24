"""CLI интерфейс для менеджера паролей."""

import argparse
import getpass
import json
import sys
from pathlib import Path
from typing import Optional

from ..storage.vault_manager import VaultManager
from ..models.password_entry import PasswordEntry
from ..utils.password_generator import generate_password, generate_passphrase
from ..utils.password_validator import validate_master_password
from ..utils.clipboard import copy_to_clipboard


def get_vault_path() -> Path:
    """Получает путь к хранилищу по умолчанию."""
    home = Path.home()
    vault_dir = home / ".password_manager"
    vault_dir.mkdir(exist_ok=True)
    return vault_dir / "vault.vault"


def get_master_password(prompt: str = "Введите мастер-пароль: ") -> str:
    """Запрашивает мастер-пароль у пользователя."""
    return getpass.getpass(prompt)


def cmd_init(args):
    """Создаёт новое хранилище."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    
    if vault_path.exists():
        print(f"Ошибка: Файл {vault_path} уже существует.")
        sys.exit(1)
    
    print("Создание нового хранилища паролей...")
    print("Введите мастер-пароль для нового хранилища.")
    
    while True:
        password = get_master_password("Мастер-пароль: ")
        is_valid, message = validate_master_password(password)
        
        if not is_valid:
            print(f"Ошибка: {message}")
            continue
        
        confirm = get_master_password("Подтвердите мастер-пароль: ")
        if password != confirm:
            print("Ошибка: Пароли не совпадают.")
            continue
        
        break
    
    try:
        VaultManager.create_vault(str(vault_path), password)
        print(f"Хранилище успешно создано: {vault_path}")
    except Exception as e:
        print(f"Ошибка при создании хранилища: {e}")
        sys.exit(1)


def cmd_add(args):
    """Добавляет новую запись."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    manager = VaultManager(str(vault_path))
    
    try:
        password = get_master_password()
        vault = manager.load_vault(password)
    except Exception as e:
        print(f"Ошибка при загрузке хранилища: {e}")
        sys.exit(1)
    
    entry = PasswordEntry()
    
    entry.title = args.title or input("Название: ")
    entry.username = args.username or input("Имя пользователя: ")
    
    if args.password:
        entry.password = args.password
    elif args.generate:
        length = args.length or 16
        entry.password = generate_password(length=length)
        print(f"Сгенерированный пароль: {entry.password}")
    else:
        entry.password = get_master_password("Пароль: ")
    
    entry.url = args.url or input("URL (опционально): ")
    entry.notes = args.notes or input("Заметки (опционально): ")
    entry.category = args.category or input("Категория (опционально): ")
    
    if args.tags:
        entry.tags = [tag.strip() for tag in args.tags.split(",")]
    
    vault.add_entry(entry)
    manager.save_vault(vault, password)
    
    print(f"Запись '{entry.title}' успешно добавлена (ID: {entry.id})")


def cmd_list(args):
    """Выводит список всех записей."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    manager = VaultManager(str(vault_path))
    
    try:
        password = get_master_password()
        vault = manager.load_vault(password)
    except Exception as e:
        print(f"Ошибка при загрузке хранилища: {e}")
        sys.exit(1)
    
    if not vault.entries:
        print("Хранилище пусто.")
        return
    
    print(f"\nВсего записей: {len(vault.entries)}\n")
    
    for i, entry in enumerate(vault.entries, 1):
        print(f"{i}. {entry.title}")
        print(f"   ID: {entry.id}")
        print(f"   Пользователь: {entry.username}")
        if entry.url:
            print(f"   URL: {entry.url}")
        if entry.category:
            print(f"   Категория: {entry.category}")
        if entry.tags:
            print(f"   Теги: {', '.join(entry.tags)}")
        print()


def cmd_get(args):
    """Показывает детали записи."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    manager = VaultManager(str(vault_path))
    
    try:
        password = get_master_password()
        vault = manager.load_vault(password)
    except Exception as e:
        print(f"Ошибка при загрузке хранилища: {e}")
        sys.exit(1)
    
    entry = vault.get_entry(args.id)
    if not entry:
        print(f"Запись с ID {args.id} не найдена.")
        sys.exit(1)
    
    print(f"\nНазвание: {entry.title}")
    print(f"ID: {entry.id}")
    print(f"Имя пользователя: {entry.username}")
    print(f"Пароль: {entry.password}")
    if entry.url:
        print(f"URL: {entry.url}")
    if entry.notes:
        print(f"Заметки: {entry.notes}")
    if entry.category:
        print(f"Категория: {entry.category}")
    if entry.tags:
        print(f"Теги: {', '.join(entry.tags)}")
    print(f"Создано: {entry.created_at}")
    print(f"Обновлено: {entry.updated_at}")
    
    if args.copy_password:
        copy_to_clipboard(entry.password)
        print("\nПароль скопирован в буфер обмена (будет очищен через 30 секунд)")


def cmd_edit(args):
    """Редактирует запись."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    manager = VaultManager(str(vault_path))
    
    try:
        password = get_master_password()
        vault = manager.load_vault(password)
    except Exception as e:
        print(f"Ошибка при загрузке хранилища: {e}")
        sys.exit(1)
    
    entry = vault.get_entry(args.id)
    if not entry:
        print(f"Запись с ID {args.id} не найдена.")
        sys.exit(1)
    
    if args.title:
        entry.title = args.title
    if args.username:
        entry.username = args.username
    if args.password:
        entry.password = args.password
    if args.url:
        entry.url = args.url
    if args.notes:
        entry.notes = args.notes
    if args.category:
        entry.category = args.category
    if args.tags:
        entry.tags = [tag.strip() for tag in args.tags.split(",")]
    
    entry.update()
    vault.update_entry(args.id, entry)
    manager.save_vault(vault, password)
    
    print(f"Запись '{entry.title}' успешно обновлена")


def cmd_delete(args):
    """Удаляет запись."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    manager = VaultManager(str(vault_path))
    
    try:
        password = get_master_password()
        vault = manager.load_vault(password)
    except Exception as e:
        print(f"Ошибка при загрузке хранилища: {e}")
        sys.exit(1)
    
    entry = vault.get_entry(args.id)
    if not entry:
        print(f"Запись с ID {args.id} не найдена.")
        sys.exit(1)
    
    confirm = input(f"Вы уверены, что хотите удалить '{entry.title}'? (yes/no): ")
    if confirm.lower() != "yes":
        print("Отменено.")
        return
    
    vault.delete_entry(args.id)
    manager.save_vault(vault, password)
    
    print(f"Запись '{entry.title}' успешно удалена")


def cmd_search(args):
    """Ищет записи по запросу."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    manager = VaultManager(str(vault_path))
    
    try:
        password = get_master_password()
        vault = manager.load_vault(password)
    except Exception as e:
        print(f"Ошибка при загрузке хранилища: {e}")
        sys.exit(1)
    
    results = vault.search(args.query)
    
    if not results:
        print(f"По запросу '{args.query}' ничего не найдено.")
        return
    
    print(f"\nНайдено записей: {len(results)}\n")
    
    for i, entry in enumerate(results, 1):
        print(f"{i}. {entry.title} (ID: {entry.id})")
        print(f"   Пользователь: {entry.username}")
        if entry.url:
            print(f"   URL: {entry.url}")
        print()


def cmd_generate(args):
    """Генерирует пароль или passphrase."""
    if args.passphrase:
        word_count = args.words or 4
        result = generate_passphrase(word_count=word_count, separator=args.separator or "-")
        print(f"Сгенерированная passphrase: {result}")
    else:
        length = args.length or 16
        result = generate_password(
            length=length,
            include_uppercase=not args.no_uppercase,
            include_lowercase=not args.no_lowercase,
            include_digits=not args.no_digits,
            include_symbols=not args.no_symbols,
            exclude_similar=not args.include_similar,
        )
        print(f"Сгенерированный пароль: {result}")
    
    if args.copy:
        copy_to_clipboard(result)
        print("Скопировано в буфер обмена (будет очищено через 30 секунд)")


def cmd_export(args):
    """Экспортирует хранилище в JSON или CSV."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    manager = VaultManager(str(vault_path))
    
    try:
        password = get_master_password()
        vault = manager.load_vault(password)
    except Exception as e:
        print(f"Ошибка при загрузке хранилища: {e}")
        sys.exit(1)
    
    output_path = Path(args.output)
    
    if args.format == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(vault.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"Хранилище экспортировано в {output_path}")
    elif args.format == "csv":
        import csv
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Username", "Password", "URL", "Notes", "Category", "Tags"])
            
            for entry in vault.entries:
                writer.writerow([
                    entry.title,
                    entry.username,
                    entry.password,
                    entry.url,
                    entry.notes,
                    entry.category,
                    ", ".join(entry.tags),
                ])
        print(f"Хранилище экспортировано в {output_path}")
    else:
        print(f"Неподдерживаемый формат: {args.format}")
        sys.exit(1)


def cmd_import(args):
    """Импортирует записи из JSON или CSV."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    manager = VaultManager(str(vault_path))
    
    try:
        password = get_master_password()
        vault = manager.load_vault(password)
    except Exception as e:
        print(f"Ошибка при загрузке хранилища: {e}")
        sys.exit(1)
    
    input_path = Path(args.input)
    
    if args.format == "json":
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        imported = 0
        for entry_data in data.get("entries", []):
            entry = PasswordEntry.from_dict(entry_data)
            try:
                vault.add_entry(entry)
                imported += 1
            except ValueError:
                # Запись уже существует, пропускаем
                pass
        
        print(f"Импортировано записей: {imported}")
    
    elif args.format == "csv":
        import csv
        
        imported = 0
        with open(input_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = PasswordEntry(
                    title=row.get("Title", ""),
                    username=row.get("Username", ""),
                    password=row.get("Password", ""),
                    url=row.get("URL", ""),
                    notes=row.get("Notes", ""),
                    category=row.get("Category", ""),
                    tags=[tag.strip() for tag in row.get("Tags", "").split(",") if tag.strip()],
                )
                try:
                    vault.add_entry(entry)
                    imported += 1
                except ValueError:
                    pass
        
        print(f"Импортировано записей: {imported}")
    
    manager.save_vault(vault, password)


def cmd_change_password(args):
    """Меняет мастер-пароль."""
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    manager = VaultManager(str(vault_path))
    
    old_password = get_master_password("Старый мастер-пароль: ")
    
    while True:
        new_password = get_master_password("Новый мастер-пароль: ")
        is_valid, message = validate_master_password(new_password)
        
        if not is_valid:
            print(f"Ошибка: {message}")
            continue
        
        confirm = get_master_password("Подтвердите новый мастер-пароль: ")
        if new_password != confirm:
            print("Ошибка: Пароли не совпадают.")
            continue
        
        break
    
    try:
        manager.change_master_password(old_password, new_password)
        print("Мастер-пароль успешно изменён.")
    except Exception as e:
        print(f"Ошибка при смене пароля: {e}")
        sys.exit(1)


def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(description="Локальный менеджер паролей")
    parser.add_argument(
        "--vault",
        help="Путь к файлу хранилища (по умолчанию: ~/.password_manager/vault.vault)",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    
    # init
    init_parser = subparsers.add_parser("init", help="Создать новое хранилище")
    
    # add
    add_parser = subparsers.add_parser("add", help="Добавить новую запись")
    add_parser.add_argument("--title", help="Название")
    add_parser.add_argument("--username", help="Имя пользователя")
    add_parser.add_argument("--password", help="Пароль")
    add_parser.add_argument("--url", help="URL")
    add_parser.add_argument("--notes", help="Заметки")
    add_parser.add_argument("--category", help="Категория")
    add_parser.add_argument("--tags", help="Теги (через запятую)")
    add_parser.add_argument("--generate", action="store_true", help="Сгенерировать пароль")
    add_parser.add_argument("--length", type=int, help="Длина генерируемого пароля")
    
    # list
    list_parser = subparsers.add_parser("list", help="Список всех записей")
    
    # get
    get_parser = subparsers.add_parser("get", help="Показать запись")
    get_parser.add_argument("id", help="ID записи")
    get_parser.add_argument("--copy-password", action="store_true", help="Скопировать пароль в буфер")
    
    # edit
    edit_parser = subparsers.add_parser("edit", help="Редактировать запись")
    edit_parser.add_argument("id", help="ID записи")
    edit_parser.add_argument("--title", help="Название")
    edit_parser.add_argument("--username", help="Имя пользователя")
    edit_parser.add_argument("--password", help="Пароль")
    edit_parser.add_argument("--url", help="URL")
    edit_parser.add_argument("--notes", help="Заметки")
    edit_parser.add_argument("--category", help="Категория")
    edit_parser.add_argument("--tags", help="Теги (через запятую)")
    
    # delete
    delete_parser = subparsers.add_parser("delete", help="Удалить запись")
    delete_parser.add_argument("id", help="ID записи")
    
    # search
    search_parser = subparsers.add_parser("search", help="Поиск записей")
    search_parser.add_argument("query", help="Поисковый запрос")
    
    # generate
    generate_parser = subparsers.add_parser("generate", help="Сгенерировать пароль")
    generate_parser.add_argument("--length", type=int, help="Длина пароля")
    generate_parser.add_argument("--no-uppercase", action="store_true", help="Без заглавных букв")
    generate_parser.add_argument("--no-lowercase", action="store_true", help="Без строчных букв")
    generate_parser.add_argument("--no-digits", action="store_true", help="Без цифр")
    generate_parser.add_argument("--no-symbols", action="store_true", help="Без символов")
    generate_parser.add_argument("--include-similar", action="store_true", help="Включить похожие символы")
    generate_parser.add_argument("--passphrase", action="store_true", help="Генерировать passphrase")
    generate_parser.add_argument("--words", type=int, help="Количество слов для passphrase")
    generate_parser.add_argument("--separator", help="Разделитель для passphrase")
    generate_parser.add_argument("--copy", action="store_true", help="Скопировать в буфер")
    
    # export
    export_parser = subparsers.add_parser("export", help="Экспортировать хранилище")
    export_parser.add_argument("output", help="Путь к выходному файлу")
    export_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Формат экспорта")
    
    # import
    import_parser = subparsers.add_parser("import", help="Импортировать записи")
    import_parser.add_argument("input", help="Путь к входному файлу")
    import_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Формат импорта")
    
    # change-password
    change_password_parser = subparsers.add_parser("change-password", help="Изменить мастер-пароль")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        "init": cmd_init,
        "add": cmd_add,
        "list": cmd_list,
        "get": cmd_get,
        "edit": cmd_edit,
        "delete": cmd_delete,
        "search": cmd_search,
        "generate": cmd_generate,
        "export": cmd_export,
        "import": cmd_import,
        "change-password": cmd_change_password,
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()

