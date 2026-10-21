"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-5 Авторизация
Модуль:      auth
Назначение:  аутентификация, блокировка после 5 неудач на 60 с
Методы:
  - is_locked — проверка временной блокировки входа для пользователя
  - get_lock_remaining_time — оставшееся время блокировки в секундах
  - record_failure — фиксация неудачной попытки входа и проверка порога блокировки
  - reset_failures — сброс счётчика неудачных попыток при успешном входе
  - authenticate — аутентификация пользователя и инициализация сеанса
  - logout — завершение сеанса пользователя
  - clear_lockouts — сброс состояния блокировок
"""
import threading
import time
from typing import Any, Dict, Optional, Tuple

from . import accounts, sessions

LOGIN_MAX_ATTEMPTS = 5
LOGIN_BLOCK_SEC = 60

_lock = threading.Lock()
_failed_attempts: Dict[str, int] = {}
_lockout_until: Dict[str, float] = {}


def is_locked(username: str) -> bool:
    """Проверка, активна ли блокировка входа для пользователя (FR-31)."""
    with _lock:
        until = _lockout_until.get(username, 0)
        if time.time() < until:
            return True
        if until > 0 and time.time() >= until:
            # Блокировка истекла, очищаем
            _lockout_until.pop(username, None)
            _failed_attempts.pop(username, None)
        return False


def get_lock_remaining_time(username: str) -> int:
    """Оставшееся время блокировки в секундах (0, если блокировка не активна)."""
    with _lock:
        until = _lockout_until.get(username, 0)
        rem = until - time.time()
        return max(0, int(rem))


def record_failure(username: str) -> Tuple[int, bool]:
    """
    Фиксация неудачной попытки входа (FR-31).
    Возвращает (текущее_число_попыток, заблокирован_ли_вход).
    """
    with _lock:
        cnt = _failed_attempts.get(username, 0) + 1
        _failed_attempts[username] = cnt
        if cnt >= LOGIN_MAX_ATTEMPTS:
            _lockout_until[username] = time.time() + LOGIN_BLOCK_SEC
            return cnt, True
        return cnt, False


def reset_failures(username: str) -> None:
    """Сброс счётчика неудачных попыток при успешном входе."""
    with _lock:
        _failed_attempts.pop(username, None)
        _lockout_until.pop(username, None)


def clear_lockouts() -> None:
    """Сброс всех блокировок и попыток (для тестов и сброса стенда)."""
    with _lock:
        _failed_attempts.clear()
        _lockout_until.clear()


def authenticate(
    username: str,
    password: str,
    source: str = "cli",
    accounts_path: str = accounts.DEFAULT_ACCOUNTS_PATH,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Аутентификация пользователя по логину и паролю (FR-30, FR-31, FR-34).
    Возвращает:
      (успех: bool,
       session_info: dict | None,
       message_code: str | None,   # "M02", "M12", "M04" и т.п.
       event_code: str | None)     # "E01", "E03", "E04", "E06"
    """
    if is_locked(username):
        return False, None, "M12", "E06"

    user = accounts.get_user(username, path=accounts_path)
    if not user:
        cnt, locked = record_failure(username)
        if locked:
            return False, None, "M12", "E06"
        return False, None, "M02", "E03"

    stored_hash = user.get("password_hash", "")
    salt = user.get("salt", "")
    iterations = user.get("iterations", accounts.DEFAULT_HASH_ITERATIONS)

    if not accounts.verify_password(password, stored_hash, salt, iterations):
        cnt, locked = record_failure(username)
        if locked:
            return False, None, "M12", "E06"
        return False, None, "M02", "E03"

    # Успешная аутентификация
    reset_failures(username)
    base_role = user.get("role", "ro")
    session, warning_code, event_code = sessions.create_session(
        username=username,
        role=base_role,
        source=source,
    )
    return True, session, warning_code, event_code


def logout(session_id: str) -> Tuple[bool, Optional[str]]:
    """
    Завершение сеанса пользователя (FR-35).
    Возвращает (успех, код события "E02").
    """
    ok, event_code = sessions.close_session(session_id, reason="logout")
    return ok, event_code or "E02"
