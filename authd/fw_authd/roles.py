"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-5 Авторизация
Модуль:      roles
Назначение:  роли rw / ro, проверка права на команду
Методы:
  - is_modifying_cmd — проверка, является ли команда изменяющей состояние
  - is_read_only_cmd — проверка, является ли команда запросом на чтение
  - check_permission — проверка прав роли на выполнение команды
  - check_session_permission — проверка прав сеанса на выполнение команды
  - validate_role_transition — валидация смены роли (защита admin)
  - get_role_permissions — получение описания прав для заданной роли
"""
from typing import Any, Dict, Optional, Set, Tuple

ROLE_RW = "rw"
ROLE_RO = "ro"
ALLOWED_ROLES = (ROLE_RW, ROLE_RO)

# Список изменяющих команд ПО МЭ (FR-32, FR-37b)
MODIFYING_COMMANDS: Set[str] = {
    # ПС-5 Учётные записи и сеансы
    "user.add",
    "user.edit",
    "user.delete",
    "session.kill",
    # ПС-1 Фильтрация
    "rule.add",
    "rule.edit",
    "rule.delete",
    "state.clear",
    # ПС-2 Журналирование
    "log.packets.clear",
    "log.flush",
    # ПС-6 Целостность
    "integrity.restore",
    "integrity.update_baseline",
    # Конфигурация и ОС
    "config.save",
    "config.apply",
    "config.reset",
    "if.set",
    "route.set",
    "time.set",
    "sys.reboot",
    "sys.shutdown",
}

# Список команд только для чтения
READ_ONLY_COMMANDS: Set[str] = {
    # ПС-5 Авторизация
    "auth.login",
    "auth.logout",
    "auth.ping",
    "auth.check",
    "user.list",
    "session.list",
    # ПС-1 Фильтрация
    "rule.list",
    "state.list",
    # ПС-2 Журналирование
    "log.query.events",
    "log.query.packets",
    # ПС-6 Целостность
    "integrity.check",
    "integrity.status",
    # Конфигурация и ОС
    "config.show",
    "if.list",
    "route.list",
    "time.get",
    "sys.info",
}


def is_modifying_cmd(cmd: str) -> bool:
    """Проверка, является ли команда изменяющей состояние (FR-32)."""
    if cmd in MODIFYING_COMMANDS:
        return True
    # Эвристика по действию команды: add, edit, delete, set, clear, restore, kill
    parts = cmd.split(".")
    if len(parts) >= 2:
        action = parts[-1]
        if action in {"add", "edit", "delete", "set", "clear", "restore", "kill", "save", "apply", "reset"}:
            return True
    return False


def is_read_only_cmd(cmd: str) -> bool:
    """Проверка, является ли команда запросом на чтение."""
    return not is_modifying_cmd(cmd)


def check_permission(role: str, cmd: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Проверка прав роли на выполнение команды (FR-32, FR-37b).
    Роль 'rw' может выполнять любые команды.
    Роль 'ro' не может выполнять изменяющие команды: возвращает (False, "M03", "E50").
    """
    if role not in ALLOWED_ROLES:
        return False, "M03", "E50"

    if role == ROLE_RW:
        return True, None, None

    # Роль ro (только чтение)
    if is_modifying_cmd(cmd):
        return False, "M03", "E50"

    return True, None, None


def check_session_permission(session: Any, cmd: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Проверка прав сеанса (словарь сеанса или идентификатор роли).
    """
    if isinstance(session, dict):
        role = session.get("effective_role") or session.get("role", ROLE_RO)
    elif isinstance(session, str):
        role = session
    else:
        return False, "M03", "E50"

    return check_permission(role, cmd)


def validate_role_transition(
    username: str,
    current_role: str,
    new_role: str,
) -> Tuple[bool, Optional[str]]:
    """
    Проверка допустимости изменения роли (FR-33).
    Предустановленному администратору 'admin' запрещено менять роль с rw (M05).
    """
    if username == "admin" and new_role != ROLE_RW:
        return False, "M05"
    if new_role not in ALLOWED_ROLES:
        return False, "M06"
    return True, None


def get_role_permissions(role: str) -> Dict[str, Any]:
    """Получение информации о правах роли."""
    can_modify = (role == ROLE_RW)
    return {
        "role": role,
        "can_modify": can_modify,
        "can_read": True,
        "allowed_categories": ["read", "write"] if can_modify else ["read"],
    }
