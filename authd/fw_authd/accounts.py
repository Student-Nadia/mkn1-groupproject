"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-5 Авторизация
Модуль:      accounts
Назначение:  учётные записи, accounts.json, PBKDF2-HMAC-SHA-256
Методы:
  - validate_username — проверка формата идентификатора пользователя
  - validate_password — проверка сложности пароля
  - validate_role — проверка допустимости роли пользователя
  - hash_password — вычисление хэша пароля с солью (PBKDF2-HMAC-SHA-256)
  - verify_password — безопасная сверка пароля с хэшем
  - load_accounts — загрузка файла учётных записей accounts.json
  - save_accounts — сохранение файла учётных записей accounts.json
  - list_users — получение списка учётных записей (без хэшей)
  - get_user — получение информации об учётной записи
  - add_user — добавление новой учётной записи
  - edit_user — изменение роли или пароля учётной записи
  - delete_user — удаление учётной записи
"""
import hashlib
import hmac
import json
import os
import re
import secrets
from typing import Any, Dict, List, Optional, Tuple

ID_MIN_LEN = 3
ID_MAX_LEN = 32
ID_PATTERN = r"^[A-Za-z0-9_]+$"
PWD_MIN_LEN = 8
PWD_MAX_LEN = 128
ALLOWED_ROLES = ("rw", "ro")
BUILTIN_ADMIN_ID = "admin"
DEFAULT_ACCOUNTS_PATH = "/etc/fw/accounts.json"
DEFAULT_HASH_ALGO = "pbkdf2_sha256"
DEFAULT_HASH_ITERATIONS = 200000
DEFAULT_SALT_BYTES = 16

_RE_USERNAME = re.compile(ID_PATTERN)

# Кэш учётных записей в памяти для стенда / тестов
_accounts_cache: Dict[str, Dict[str, Any]] = {}


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """Проверка формата идентификатора пользователя (FR-36)."""
    if not isinstance(username, str):
        return False, "M06"
    if not (ID_MIN_LEN <= len(username) <= ID_MAX_LEN):
        return False, "M06"
    if not _RE_USERNAME.match(username):
        return False, "M06"
    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """Проверка длины пароля (FR-36)."""
    if not isinstance(password, str):
        return False, "M06"
    if not (PWD_MIN_LEN <= len(password) <= PWD_MAX_LEN):
        return False, "M06"
    return True, None


def validate_role(role: str) -> Tuple[bool, Optional[str]]:
    """Проверка допустимости роли пользователя (FR-36)."""
    if role not in ALLOWED_ROLES:
        return False, "M06"
    return True, None


def hash_password(
    password: str,
    salt_hex: Optional[str] = None,
    iterations: int = DEFAULT_HASH_ITERATIONS,
) -> Tuple[str, str]:
    """Вычисление хэша пароля с солью по алгоритму PBKDF2-HMAC-SHA-256 (FR-37)."""
    if salt_hex is None:
        salt_bytes = secrets.token_bytes(DEFAULT_SALT_BYTES)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt_hex)

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        iterations,
    )
    return derived.hex(), salt_hex


def verify_password(
    password: str,
    stored_hash_hex: str,
    salt_hex: str,
    iterations: int = DEFAULT_HASH_ITERATIONS,
) -> bool:
    """Безопасная сверка пароля с сохранённым хэшем без утечки по времени (FR-37)."""
    computed_hash_hex, _ = hash_password(password, salt_hex, iterations)
    return hmac.compare_digest(computed_hash_hex, stored_hash_hex)


def load_accounts(path: str = DEFAULT_ACCOUNTS_PATH) -> Dict[str, Dict[str, Any]]:
    """Загрузка файла учётных записей accounts.json."""
    global _accounts_cache
    if not os.path.exists(path):
        # Если файла нет, возвращаем текущий кэш или пустой словарь
        return _accounts_cache
    try:
        with open(path, "r", encoding="utf-8") as f:
            _accounts_cache = json.load(f)
            return _accounts_cache
    except Exception:
        return _accounts_cache


def save_accounts(
    accounts: Dict[str, Dict[str, Any]],
    path: str = DEFAULT_ACCOUNTS_PATH,
) -> None:
    """Сохранение словаря учётных записей в accounts.json."""
    global _accounts_cache
    _accounts_cache = accounts
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)


def get_user(username: str, path: str = DEFAULT_ACCOUNTS_PATH) -> Optional[Dict[str, Any]]:
    """Получение записи пользователя по идентификатору."""
    accounts = load_accounts(path)
    user = accounts.get(username)
    if user is not None:
        return dict(user)
    return None


def list_users(path: str = DEFAULT_ACCOUNTS_PATH) -> List[Dict[str, str]]:
    """Получение списка учётных записей без вывода паролей и хэшей (FR-37)."""
    accounts = load_accounts(path)
    return [
        {"id": uid, "role": udata.get("role", "ro")}
        for uid, udata in accounts.items()
    ]


def add_user(
    username: str,
    password: str,
    role: str,
    path: str = DEFAULT_ACCOUNTS_PATH,
) -> Tuple[bool, Optional[str]]:
    """
    Добавление новой учётной записи (FR-36).
    Возвращает (успех, код ошибки M..).
    """
    ok, err = validate_username(username)
    if not ok:
        return False, err
    ok, err = validate_password(password)
    if not ok:
        return False, err
    ok, err = validate_role(role)
    if not ok:
        return False, err

    accounts = load_accounts(path)
    if username in accounts:
        return False, "M06"

    p_hash, salt = hash_password(password)
    accounts[username] = {
        "role": role,
        "password_hash": p_hash,
        "salt": salt,
        "iterations": DEFAULT_HASH_ITERATIONS,
        "builtin": (username == BUILTIN_ADMIN_ID),
    }
    save_accounts(accounts, path)
    return True, None


def edit_user(
    username: str,
    new_password: Optional[str] = None,
    new_role: Optional[str] = None,
    path: str = DEFAULT_ACCOUNTS_PATH,
) -> Tuple[bool, Optional[str]]:
    """
    Изменение роли или пароля учётной записи (FR-33, FR-36).
    Запрещено менять роль предустановленного admin (M05).
    """
    accounts = load_accounts(path)
    user = accounts.get(username)
    if user is None:
        return False, "M06"

    # Запрет изменения роли для предустановленного администратора (FR-33)
    if new_role is not None:
        if username == BUILTIN_ADMIN_ID and new_role != "rw":
            return False, "M05"
        ok, err = validate_role(new_role)
        if not ok:
            return False, err
        user["role"] = new_role

    if new_password is not None:
        ok, err = validate_password(new_password)
        if not ok:
            return False, err
        p_hash, salt = hash_password(new_password)
        user["password_hash"] = p_hash
        user["salt"] = salt

    accounts[username] = user
    save_accounts(accounts, path)
    return True, None


def delete_user(
    username: str,
    path: str = DEFAULT_ACCOUNTS_PATH,
) -> Tuple[bool, Optional[str]]:
    """
    Удаление учётной записи (FR-33).
    Удаление предустановленного admin блокируется с M05.
    """
    if username == BUILTIN_ADMIN_ID:
        return False, "M05"

    accounts = load_accounts(path)
    if username not in accounts:
        return False, "M06"

    del accounts[username]
    save_accounts(accounts, path)
    return True, None
