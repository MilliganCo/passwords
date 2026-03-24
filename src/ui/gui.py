"""GUI интерфейс для менеджера паролей на tkinter."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import getpass
import threading
from pathlib import Path
from datetime import datetime, timedelta
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


class LoginWindow:
    """Окно входа в хранилище."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Менеджер паролей - Вход")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        self.vault_path = get_vault_path()
        self.master_password: Optional[str] = None
        self.manager: Optional[VaultManager] = None
        
        self.setup_ui()
        
        # Центрируем окно
        self.center_window()
    
    def center_window(self):
        """Центрирует окно на экране."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """Настраивает интерфейс."""
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Путь к хранилищу
        ttk.Label(frame, text=f"Хранилище: {self.vault_path}").pack(pady=5)
        
        # Поле для пароля
        ttk.Label(frame, text="Мастер-пароль:").pack(anchor=tk.W, pady=5)
        self.password_entry = ttk.Entry(frame, show="*", width=30)
        self.password_entry.pack(pady=5)
        self.password_entry.bind("<Return>", lambda e: self.login())
        self.password_entry.focus()
        
        # Кнопки
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Войти", command=self.login).pack(side=tk.LEFT, padx=5)
        
        if not self.vault_path.exists():
            ttk.Button(button_frame, text="Создать новое", command=self.create_new).pack(side=tk.LEFT, padx=5)
    
    def login(self):
        """Выполняет вход в хранилище."""
        password = self.password_entry.get()
        if not password:
            messagebox.showerror("Ошибка", "Введите мастер-пароль")
            return
        
        try:
            manager = VaultManager(str(self.vault_path))
            vault = manager.load_vault(password)
            self.master_password = password
            self.manager = manager
            
            # Закрываем окно входа и открываем главное окно
            self.root.destroy()
            MainWindow(self.master_password, self.manager)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть хранилище:\n{e}")
    
    def create_new(self):
        """Создаёт новое хранилище."""
        dialog = CreateVaultDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.created:
            self.login()


class CreateVaultDialog:
    """Диалог создания нового хранилища."""
    
    def __init__(self, parent):
        self.created = False
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Создать новое хранилище")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Введите мастер-пароль для нового хранилища:").pack(pady=5)
        
        ttk.Label(frame, text="Мастер-пароль:").pack(anchor=tk.W, pady=5)
        self.password_entry = ttk.Entry(frame, show="*", width=30)
        self.password_entry.pack(pady=5)
        
        ttk.Label(frame, text="Подтвердите пароль:").pack(anchor=tk.W, pady=5)
        self.confirm_entry = ttk.Entry(frame, show="*", width=30)
        self.confirm_entry.pack(pady=5)
        
        self.status_label = ttk.Label(frame, text="", foreground="red")
        self.status_label.pack(pady=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Создать", command=self.create).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        self.password_entry.focus()
    
    def create(self):
        """Создаёт хранилище."""
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        
        if not password:
            self.status_label.config(text="Введите пароль")
            return
        
        if password != confirm:
            self.status_label.config(text="Пароли не совпадают")
            return
        
        is_valid, message = validate_master_password(password)
        if not is_valid:
            self.status_label.config(text=message)
            return
        
        try:
            VaultManager.create_vault(str(get_vault_path()), password)
            self.created = True
            self.dialog.destroy()
        except Exception as e:
            self.status_label.config(text=f"Ошибка: {e}")


class MainWindow:
    """Главное окно приложения."""
    
    def __init__(self, master_password: str, manager: VaultManager):
        self.master_password = master_password
        self.manager = manager
        self.vault = manager.load_vault(master_password)
        
        self.root = tk.Tk()
        self.root.title("Менеджер паролей")
        self.root.geometry("900x600")
        
        # Авто-лок
        self.auto_lock_timeout = 300  # 5 минут
        self.last_activity = datetime.now()
        self.auto_lock_timer = None
        self.start_auto_lock_timer()
        
        # Привязка событий для отслеживания активности
        self.root.bind("<KeyPress>", self.reset_auto_lock)
        self.root.bind("<ButtonPress>", self.reset_auto_lock)
        
        self.setup_ui()
        self.refresh_list()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Настраивает интерфейс главного окна."""
        # Меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Сохранить", command=self.save_vault)
        file_menu.add_command(label="Изменить мастер-пароль", command=self.change_password)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Генератор паролей", command=self.show_password_generator)
        tools_menu.add_command(label="Настройки авто-лока", command=self.show_auto_lock_settings)
        
        # Панель поиска
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())
        
        ttk.Button(search_frame, text="Очистить", command=self.clear_search).pack(side=tk.LEFT, padx=5)
        
        # Основная область
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Список записей
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(list_frame, text="Записи:").pack(anchor=tk.W)
        
        # Treeview для списка
        columns = ("title", "username", "category")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=20)
        self.tree.heading("#0", text="ID")
        self.tree.heading("title", text="Название")
        self.tree.heading("username", text="Пользователь")
        self.tree.heading("category", text="Категория")
        
        self.tree.column("#0", width=100)
        self.tree.column("title", width=200)
        self.tree.column("username", width=150)
        self.tree.column("category", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", lambda e: self.edit_entry())
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Кнопки действий
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        ttk.Button(button_frame, text="Добавить", command=self.add_entry, width=20).pack(pady=5)
        ttk.Button(button_frame, text="Редактировать", command=self.edit_entry, width=20).pack(pady=5)
        ttk.Button(button_frame, text="Удалить", command=self.delete_entry, width=20).pack(pady=5)
        ttk.Button(button_frame, text="Показать пароль", command=self.show_password, width=20).pack(pady=5)
        ttk.Button(button_frame, text="Копировать пароль", command=self.copy_password, width=20).pack(pady=5)
    
    def refresh_list(self):
        """Обновляет список записей."""
        # Очищаем дерево
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Фильтруем записи
        query = self.search_entry.get().strip()
        if query:
            entries = self.vault.search(query)
        else:
            entries = self.vault.entries
        
        # Добавляем записи
        for entry in entries:
            self.tree.insert(
                "",
                tk.END,
                text=entry.id[:8] + "...",
                values=(entry.title, entry.username, entry.category),
                tags=(entry.id,),
            )
    
    def clear_search(self):
        """Очищает поле поиска."""
        self.search_entry.delete(0, tk.END)
        self.refresh_list()
    
    def get_selected_entry(self) -> Optional[PasswordEntry]:
        """Получает выбранную запись."""
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = self.tree.item(selection[0])
        entry_id = item["tags"][0]
        return self.vault.get_entry(entry_id)
    
    def add_entry(self):
        """Добавляет новую запись."""
        dialog = EntryDialog(self.root, None)
        self.root.wait_window(dialog.dialog)
        
        if dialog.entry:
            self.vault.add_entry(dialog.entry)
            self.save_vault()
            self.refresh_list()
    
    def edit_entry(self):
        """Редактирует выбранную запись."""
        entry = self.get_selected_entry()
        if not entry:
            messagebox.showwarning("Предупреждение", "Выберите запись для редактирования")
            return
        
        dialog = EntryDialog(self.root, entry)
        self.root.wait_window(dialog.dialog)
        
        if dialog.entry:
            self.vault.update_entry(entry.id, dialog.entry)
            self.save_vault()
            self.refresh_list()
    
    def delete_entry(self):
        """Удаляет выбранную запись."""
        entry = self.get_selected_entry()
        if not entry:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить запись '{entry.title}'?"):
            self.vault.delete_entry(entry.id)
            self.save_vault()
            self.refresh_list()
    
    def show_password(self):
        """Показывает пароль выбранной записи."""
        entry = self.get_selected_entry()
        if not entry:
            messagebox.showwarning("Предупреждение", "Выберите запись")
            return
        
        messagebox.showinfo("Пароль", f"Пароль для '{entry.title}':\n{entry.password}")
    
    def copy_password(self):
        """Копирует пароль в буфер обмена."""
        entry = self.get_selected_entry()
        if not entry:
            messagebox.showwarning("Предупреждение", "Выберите запись")
            return
        
        copy_to_clipboard(entry.password)
        messagebox.showinfo("Успех", "Пароль скопирован в буфер обмена (будет очищен через 30 секунд)")
    
    def show_context_menu(self, event):
        """Показывает контекстное меню."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Редактировать", command=self.edit_entry)
            menu.add_command(label="Удалить", command=self.delete_entry)
            menu.add_command(label="Показать пароль", command=self.show_password)
            menu.add_command(label="Копировать пароль", command=self.copy_password)
            menu.post(event.x_root, event.y_root)
    
    def show_password_generator(self):
        """Показывает генератор паролей."""
        dialog = PasswordGeneratorDialog(self.root)
        self.root.wait_window(dialog.dialog)
    
    def show_auto_lock_settings(self):
        """Показывает настройки авто-лока."""
        dialog = AutoLockSettingsDialog(self.root, self.auto_lock_timeout)
        self.root.wait_window(dialog.dialog)
        
        if dialog.timeout is not None:
            self.auto_lock_timeout = dialog.timeout
            self.start_auto_lock_timer()
    
    def change_password(self):
        """Меняет мастер-пароль."""
        dialog = ChangePasswordDialog(self.root, self.master_password)
        self.root.wait_window(dialog.dialog)
        
        if dialog.changed:
            self.master_password = dialog.new_password
            self.save_vault()
            messagebox.showinfo("Успех", "Мастер-пароль успешно изменён")
    
    def save_vault(self):
        """Сохраняет хранилище."""
        try:
            self.manager.save_vault(self.vault, self.master_password)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить хранилище:\n{e}")
    
    def reset_auto_lock(self, event=None):
        """Сбрасывает таймер авто-лока."""
        self.last_activity = datetime.now()
        self.start_auto_lock_timer()
    
    def start_auto_lock_timer(self):
        """Запускает таймер авто-лока."""
        if self.auto_lock_timer:
            self.root.after_cancel(self.auto_lock_timer)
        
        if self.auto_lock_timeout > 0:
            self.auto_lock_timer = self.root.after(
                self.auto_lock_timeout * 1000, self.auto_lock
            )
    
    def auto_lock(self):
        """Автоматически блокирует хранилище."""
        if messagebox.askyesno("Авто-лок", "Хранилище будет заблокировано. Продолжить?"):
            self.on_closing()
    
    def on_closing(self):
        """Обработка закрытия окна."""
        self.save_vault()
        self.manager.lock()
        self.root.destroy()
        LoginWindow(tk.Tk())
    
    def run(self):
        """Запускает главный цикл."""
        self.root.mainloop()


class EntryDialog:
    """Диалог добавления/редактирования записи."""
    
    def __init__(self, parent, entry: Optional[PasswordEntry]):
        self.original_entry = entry
        self.entry = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактировать запись" if entry else "Добавить запись")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Поля
        ttk.Label(frame, text="Название:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_entry = ttk.Entry(frame, width=40)
        self.title_entry.grid(row=0, column=1, pady=5)
        if entry:
            self.title_entry.insert(0, entry.title)
        
        ttk.Label(frame, text="Имя пользователя:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(frame, width=40)
        self.username_entry.grid(row=1, column=1, pady=5)
        if entry:
            self.username_entry.insert(0, entry.username)
        
        ttk.Label(frame, text="Пароль:").grid(row=2, column=0, sticky=tk.W, pady=5)
        password_frame = ttk.Frame(frame)
        password_frame.grid(row=2, column=1, pady=5, sticky=tk.W)
        self.password_entry = ttk.Entry(password_frame, show="*", width=30)
        self.password_entry.pack(side=tk.LEFT)
        if entry:
            self.password_entry.insert(0, entry.password)
        ttk.Button(password_frame, text="Генерировать", command=self.generate_password).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame, text="URL:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(frame, width=40)
        self.url_entry.grid(row=3, column=1, pady=5)
        if entry:
            self.url_entry.insert(0, entry.url)
        
        ttk.Label(frame, text="Заметки:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.notes_text = tk.Text(frame, width=40, height=5)
        self.notes_text.grid(row=4, column=1, pady=5)
        if entry:
            self.notes_text.insert("1.0", entry.notes)
        
        ttk.Label(frame, text="Категория:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.category_entry = ttk.Entry(frame, width=40)
        self.category_entry.grid(row=5, column=1, pady=5)
        if entry:
            self.category_entry.insert(0, entry.category)
        
        ttk.Label(frame, text="Теги (через запятую):").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.tags_entry = ttk.Entry(frame, width=40)
        self.tags_entry.grid(row=6, column=1, pady=5)
        if entry:
            self.tags_entry.insert(0, ", ".join(entry.tags))
        
        # Кнопки
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        self.title_entry.focus()
    
    def generate_password(self):
        """Генерирует пароль."""
        dialog = PasswordGeneratorDialog(self.dialog)
        self.dialog.wait_window(dialog.dialog)
        if dialog.password:
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, dialog.password)
    
    def save(self):
        """Сохраняет запись."""
        if not self.title_entry.get():
            messagebox.showerror("Ошибка", "Введите название")
            return
        
        if self.original_entry:
            # Редактирование существующей записи
            self.original_entry.title = self.title_entry.get()
            self.original_entry.username = self.username_entry.get()
            self.original_entry.password = self.password_entry.get()
            self.original_entry.url = self.url_entry.get()
            self.original_entry.notes = self.notes_text.get("1.0", tk.END).strip()
            self.original_entry.category = self.category_entry.get()
            self.original_entry.tags = [tag.strip() for tag in self.tags_entry.get().split(",") if tag.strip()]
            self.original_entry.update()
            self.entry = self.original_entry
        else:
            # Создание новой записи
            self.entry = PasswordEntry(
                title=self.title_entry.get(),
                username=self.username_entry.get(),
                password=self.password_entry.get(),
                url=self.url_entry.get(),
                notes=self.notes_text.get("1.0", tk.END).strip(),
                category=self.category_entry.get(),
                tags=[tag.strip() for tag in self.tags_entry.get().split(",") if tag.strip()],
            )
        
        self.dialog.destroy()


class PasswordGeneratorDialog:
    """Диалог генератора паролей."""
    
    def __init__(self, parent):
        self.password = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Генератор паролей")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Тип генерации
        self.mode = tk.StringVar(value="password")
        ttk.Radiobutton(frame, text="Пароль", variable=self.mode, value="password").pack(anchor=tk.W)
        ttk.Radiobutton(frame, text="Passphrase", variable=self.mode, value="passphrase").pack(anchor=tk.W)
        
        # Параметры для пароля
        self.length_var = tk.IntVar(value=16)
        length_frame = ttk.Frame(frame)
        length_frame.pack(anchor=tk.W, pady=5)
        ttk.Label(length_frame, text="Длина:").pack(side=tk.LEFT)
        length_scale = ttk.Scale(length_frame, from_=8, to=64, variable=self.length_var, orient=tk.HORIZONTAL, length=200)
        length_scale.pack(side=tk.LEFT, padx=5)
        self.length_label = ttk.Label(length_frame, text="16")
        self.length_label.pack(side=tk.LEFT)
        length_scale.configure(command=lambda v: self.length_label.config(text=str(int(float(v)))))
        
        # Параметры для passphrase
        self.words_var = tk.IntVar(value=4)
        words_frame = ttk.Frame(frame)
        words_frame.pack(anchor=tk.W, pady=5)
        ttk.Label(words_frame, text="Слов:").pack(side=tk.LEFT)
        words_scale = ttk.Scale(words_frame, from_=3, to=10, variable=self.words_var, orient=tk.HORIZONTAL, length=200)
        words_scale.pack(side=tk.LEFT, padx=5)
        self.words_label = ttk.Label(words_frame, text="4")
        self.words_label.pack(side=tk.LEFT)
        words_scale.configure(command=lambda v: self.words_label.config(text=str(int(float(v)))))
        
        # Результат
        ttk.Label(frame, text="Результат:").pack(anchor=tk.W, pady=5)
        self.result_entry = ttk.Entry(frame, width=40)
        self.result_entry.pack(pady=5)
        
        # Кнопки
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Сгенерировать", command=self.generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Использовать", command=self.use_password).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def generate(self):
        """Генерирует пароль или passphrase."""
        if self.mode.get() == "passphrase":
            result = generate_passphrase(word_count=self.words_var.get())
        else:
            result = generate_password(length=self.length_var.get())
        
        self.result_entry.delete(0, tk.END)
        self.result_entry.insert(0, result)
    
    def use_password(self):
        """Использует сгенерированный пароль."""
        self.password = self.result_entry.get()
        if self.password:
            self.dialog.destroy()


class AutoLockSettingsDialog:
    """Диалог настроек авто-лока."""
    
    def __init__(self, parent, current_timeout: int):
        self.timeout = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Настройки авто-лока")
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Таймаут авто-лока (секунды):").pack(pady=5)
        
        self.timeout_var = tk.IntVar(value=current_timeout)
        timeout_entry = ttk.Entry(frame, textvariable=self.timeout_var, width=20)
        timeout_entry.pack(pady=5)
        
        ttk.Label(frame, text="0 = отключить авто-лок", foreground="gray").pack()
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def save(self):
        """Сохраняет настройки."""
        self.timeout = self.timeout_var.get()
        self.dialog.destroy()


class ChangePasswordDialog:
    """Диалог смены мастер-пароля."""
    
    def __init__(self, parent, current_password: str):
        self.changed = False
        self.new_password = None
        self.current_password = current_password
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Изменить мастер-пароль")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Старый мастер-пароль:").pack(anchor=tk.W, pady=5)
        self.old_entry = ttk.Entry(frame, show="*", width=30)
        self.old_entry.pack(pady=5)
        
        ttk.Label(frame, text="Новый мастер-пароль:").pack(anchor=tk.W, pady=5)
        self.new_entry = ttk.Entry(frame, show="*", width=30)
        self.new_entry.pack(pady=5)
        
        ttk.Label(frame, text="Подтвердите новый пароль:").pack(anchor=tk.W, pady=5)
        self.confirm_entry = ttk.Entry(frame, show="*", width=30)
        self.confirm_entry.pack(pady=5)
        
        self.status_label = ttk.Label(frame, text="", foreground="red")
        self.status_label.pack(pady=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Изменить", command=self.change).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def change(self):
        """Меняет пароль."""
        old = self.old_entry.get()
        new = self.new_entry.get()
        confirm = self.confirm_entry.get()
        
        if old != self.current_password:
            self.status_label.config(text="Неверный старый пароль")
            return
        
        if new != confirm:
            self.status_label.config(text="Пароли не совпадают")
            return
        
        is_valid, message = validate_master_password(new)
        if not is_valid:
            self.status_label.config(text=message)
            return
        
        self.new_password = new
        self.changed = True
        self.dialog.destroy()


def main():
    """Главная функция GUI."""
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

