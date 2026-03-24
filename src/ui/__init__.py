"""Интерфейсы пользователя."""

from .cli import main as cli_main
from .gui import main as gui_main

__all__ = ["cli_main", "gui_main"]

