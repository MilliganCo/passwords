"""Управление буфером обмена с автоочисткой."""

import threading
import time
import platform


def _get_clipboard():
    """Получает объект для работы с буфером обмена в зависимости от ОС."""
    system = platform.system()
    
    if system == "Windows":
        try:
            import win32clipboard
            return "win32", win32clipboard
        except ImportError:
            # Fallback на pyperclip
            try:
                import pyperclip
                return "pyperclip", pyperclip
            except ImportError:
                raise ImportError(
                    "Для работы с буфером обмена на Windows установите "
                    "pywin32 или pyperclip: pip install pywin32 или pip install pyperclip"
                )
    elif system == "Darwin":  # macOS
        try:
            import subprocess
            return "pbcopy", subprocess
        except ImportError:
            raise ImportError("Не удалось импортировать subprocess для macOS")
    else:  # Linux и другие
        try:
            import subprocess
            return "xclip", subprocess
        except ImportError:
            try:
                import pyperclip
                return "pyperclip", pyperclip
            except ImportError:
                raise ImportError(
                    "Для работы с буфером обмена на Linux установите "
                    "xclip или pyperclip: sudo apt-get install xclip или pip install pyperclip"
                )


def copy_to_clipboard(text: str, timeout: int = 30) -> None:
    """
    Копирует текст в буфер обмена и автоматически очищает его через указанное время.
    
    Args:
        text: Текст для копирования
        timeout: Время в секундах до автоматической очистки (по умолчанию 30)
    """
    system = platform.system()
    
    try:
        clipboard_type, clipboard_obj = _get_clipboard()
    except ImportError as e:
        print(f"Предупреждение: {e}")
        print(f"Текст для копирования: {text}")
        return
    
    # Копируем текст
    if clipboard_type == "win32":
        clipboard_obj.OpenClipboard()
        clipboard_obj.EmptyClipboard()
        clipboard_obj.SetClipboardText(text)
        clipboard_obj.CloseClipboard()
    elif clipboard_type == "pbcopy":  # macOS
        process = clipboard_obj.Popen(["pbcopy"], stdin=clipboard_obj.PIPE)
        process.communicate(text.encode("utf-8"))
    elif clipboard_type == "xclip":  # Linux
        process = clipboard_obj.Popen(["xclip", "-selection", "clipboard"], stdin=clipboard_obj.PIPE)
        process.communicate(text.encode("utf-8"))
    elif clipboard_type == "pyperclip":
        clipboard_obj.copy(text)
    
    # Запускаем таймер для очистки
    def clear_clipboard():
        time.sleep(timeout)
        try:
            if clipboard_type == "win32":
                clipboard_obj.OpenClipboard()
                clipboard_obj.EmptyClipboard()
                clipboard_obj.CloseClipboard()
            elif clipboard_type == "pbcopy":
                process = clipboard_obj.Popen(["pbcopy"], stdin=clipboard_obj.PIPE)
                process.communicate(b"")
            elif clipboard_type == "xclip":
                process = clipboard_obj.Popen(["xclip", "-selection", "clipboard"], stdin=clipboard_obj.PIPE)
                process.communicate(b"")
            elif clipboard_type == "pyperclip":
                clipboard_obj.copy("")
        except Exception:
            # Игнорируем ошибки при очистке (буфер мог быть изменён пользователем)
            pass
    
    thread = threading.Thread(target=clear_clipboard, daemon=True)
    thread.start()

