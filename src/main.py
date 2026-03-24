"""Главная точка входа для менеджера паролей."""

import sys
import os
import argparse

# Добавляем родительскую директорию в путь для импортов
if __name__ == "__main__":
    # Если запускается как скрипт, добавляем путь к корню проекта
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Используем абсолютные импорты при запуске как скрипт
    from src.ui.cli import main as cli_main
    from src.ui.gui import main as gui_main
else:
    # Используем относительные импорты при запуске как модуль
    from .ui.cli import main as cli_main
    from .ui.gui import main as gui_main


def main():
    """Главная функция приложения."""
    parser = argparse.ArgumentParser(description="Локальный менеджер паролей")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Запустить CLI интерфейс",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Запустить GUI интерфейс (по умолчанию)",
    )
    
    args, remaining_args = parser.parse_known_args()
    
    # Если указан --cli, передаём управление CLI
    if args.cli:
        # Передаём оставшиеся аргументы в CLI
        sys.argv = [sys.argv[0]] + remaining_args
        cli_main()
    else:
        # По умолчанию запускаем GUI
        gui_main()


if __name__ == "__main__":
    main()

