"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-5 Авторизация
Модуль:      main
Назначение:  точка входа fw-authd, сервер Unix-сокета, маршрутизация команд
Методы:
  - dispatch_request — диспетчеризация входящих запросов по протоколу JSON
  - emit_event — отправка события аудита в ПС-2 (logd)
  - notify_integrity — уведомление ПС-6 (integrityd) об обновлении эталона
  - handle_auth_login — обработка команды auth.login
  - handle_auth_logout — обработка команды auth.logout
  - handle_auth_ping — обработка команды auth.ping
  - handle_auth_check — обработка команды auth.check
  - handle_user_list — обработка команды user.list
  - handle_user_add — обработка команды user.add
  - handle_user_edit — обработка команды user.edit
  - handle_user_delete — обработка команды user.delete
  - handle_session_list — обработка команды session.list
  - handle_session_kill — обработка команды session.kill
  - start_server — запуск сервера Unix-сокета
  - main — точка входа сервиса
"""
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, Optional, Tuple

try:
    from fwcommon import codes, protocol
except ImportError:
    # Запасной вариант при относительном импорте
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "common")))
    from fwcommon import codes, protocol

from . import accounts, auth, roles, sessions

SOCKET_PATH = "/run/fw/authd.sock"
LOGD_SOCKET = "/run/fw/logd.sock"
INTEGRITYD_SOCKET = "/run/fw/integrityd.sock"
DEFAULT_CONFIG_PATH = "/etc/fw/config.json"

logger = logging.getLogger("fw_authd")

# Очередь неотправленных событий при недоступности ПС-2 (FR-28, max 1000)
_event_queue: list = []
_event_queue_lock = threading.Lock()


def emit_event(code: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Отправка события в ПС-2 (logd) по сокету /run/fw/logd.sock.
    При недоступности ПС-2 события сохраняются в очереди (до 1000) (FR-28).
    """
    payload = {"code": code, "details": details or {}}
    msg = protocol.make_msg("event", "authd", "logd", cmd="log.write.event", payload=payload)

    with _event_queue_lock:
        if len(_event_queue) < 1000:
            _event_queue.append(msg)
        else:
            # Очередь переполнена
            pass

    # Попытка сбросить очередь
    _flush_event_queue()


def _flush_event_queue() -> None:
    """Фоновая попытка отправки накопившихся событий в ПС-2."""
    if not os.path.exists(LOGD_SOCKET):
        return
    with _event_queue_lock:
        while _event_queue:
            msg = _event_queue[0]
            try:
                protocol._exchange(LOGD_SOCKET, msg, timeout=1.0)
                _event_queue.pop(0)
            except Exception:
                break


def notify_integrity() -> None:
    """
    Уведомление ПС-6 (integrityd) об изменении учётных записей:
    integrity.update_baseline.
    """
    if not os.path.exists(INTEGRITYD_SOCKET):
        return
    try:
        protocol.request(INTEGRITYD_SOCKET, "authd", "integrityd", "integrity.update_baseline", payload={})
    except Exception as e:
        logger.warning("Failed to notify integrityd: %s", e)


def _check_caller_permission(payload: Dict[str, Any], cmd: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Проверка прав инициатора запроса на выполнение команды cmd."""
    session_id = payload.get("session_id")
    if not session_id:
        return False, "M03", "E50"
    session = sessions.get_session(session_id)
    if not session:
        return False, "M15", "E07"
    allowed, err_code, event_code = roles.check_permission(session.get("effective_role", "ro"), cmd)
    return allowed, err_code, event_code


def handle_auth_login(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды auth.login (FR-30, FR-31, FR-34)."""
    username = payload.get("id") or payload.get("username", "")
    password = payload.get("password", "")
    source = payload.get("source", "cli")

    ok, session, msg_code, event_code = auth.authenticate(username, password, source=source)
    if not ok:
        if event_code:
            emit_event(event_code, {"id": username, "source": source})
        err_msg = codes.message_text(msg_code) if msg_code else "Authentication failed"
        return "error", {}, msg_code, err_msg

    if event_code:
        emit_event(event_code, {"id": username, "source": source, "role": session.get("effective_role")})

    resp_payload = {
        "session_id": session["session_id"],
        "username": session["username"],
        "role": session["effective_role"],
        "downgraded": session.get("downgraded", False),
    }
    if msg_code:
        resp_payload["warning"] = msg_code
        resp_payload["warning_message"] = codes.message_text(msg_code)

    return "ok", resp_payload, None, None


def handle_auth_logout(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды auth.logout (FR-35, E02)."""
    session_id = payload.get("session_id", "")
    session = sessions.get_session(session_id)
    ok, ev = auth.logout(session_id)
    if ok and session:
        emit_event(ev or "E02", {"id": session.get("username"), "session_id": session_id})
    return "ok", {"status": "logged_out"}, None, None


def handle_auth_ping(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды auth.ping (FR-37a)."""
    session_id = payload.get("session_id", "")
    if not sessions.touch_session(session_id):
        return "error", {}, "M15", codes.message_text("M15", reason="таймаут бездействия")
    return "ok", {"status": "pong"}, None, None


def handle_auth_check(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды auth.check (FR-32, FR-37b)."""
    target_cmd = payload.get("cmd", "")
    session_id = payload.get("session_id")
    role = payload.get("role")

    if session_id:
        sess = sessions.get_session(session_id)
        if not sess:
            return "error", {"allowed": False}, "M15", codes.message_text("M15", reason="сеанс не найден")
        role = sess.get("effective_role", "ro")

    if not role:
        return "error", {"allowed": False}, "M03", codes.message_text("M03")

    allowed, err_c, ev_c = roles.check_permission(role, target_cmd)
    if not allowed:
        emit_event(ev_c or "E50", {"cmd": target_cmd, "role": role})
        return "error", {"allowed": False}, err_c, codes.message_text(err_c)

    return "ok", {"allowed": True}, None, None


def handle_user_list(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды user.list."""
    allowed, err_c, ev_c = _check_caller_permission(payload, "user.list")
    if not allowed:
        return "error", {}, err_c, codes.message_text(err_c)

    users = accounts.list_users()
    return "ok", {"users": users}, None, None


def handle_user_add(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды user.add (FR-36, E32)."""
    allowed, err_c, ev_c = _check_caller_permission(payload, "user.add")
    if not allowed:
        return "error", {}, err_c, codes.message_text(err_c)

    uid = payload.get("id", "")
    pwd = payload.get("password", "")
    role = payload.get("role", "")

    ok, err = accounts.add_user(uid, pwd, role)
    if not ok:
        return "error", {}, err, codes.message_text(err, field="account", allowed="rw, ro")

    emit_event("E32", {"action": "add", "id": uid, "role": role})
    notify_integrity()
    return "ok", {"message": codes.message_text("M09")}, None, None


def handle_user_edit(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды user.edit (FR-33, FR-36, E32)."""
    allowed, err_c, ev_c = _check_caller_permission(payload, "user.edit")
    if not allowed:
        return "error", {}, err_c, codes.message_text(err_c)

    uid = payload.get("id", "")
    pwd = payload.get("password")
    role = payload.get("role")

    ok, err = accounts.edit_user(uid, new_password=pwd, new_role=role)
    if not ok:
        if err == "M05":
            return "error", {}, "M05", codes.message_text("M05")
        return "error", {}, err, codes.message_text(err, field="account", allowed="rw, ro")

    emit_event("E32", {"action": "edit", "id": uid, "role": role})
    notify_integrity()
    return "ok", {"message": codes.message_text("M09")}, None, None


def handle_user_delete(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды user.delete (FR-33, FR-35, E07, E32)."""
    allowed, err_c, ev_c = _check_caller_permission(payload, "user.delete")
    if not allowed:
        return "error", {}, err_c, codes.message_text(err_c)

    uid = payload.get("id", "")
    ok, err = accounts.delete_user(uid)
    if not ok:
        if err == "M05":
            return "error", {}, "M05", codes.message_text("M05")
        return "error", {}, err, codes.message_text(err, field="id", allowed="существующий пользователь кроме admin")

    # Сброс активных сеансов удалённого пользователя (FR-35, E07)
    closed = sessions.close_sessions_for_user(uid, reason="user_deleted")
    for sid in closed:
        emit_event("E07", {"id": uid, "session_id": sid, "reason": "user_deleted"})

    emit_event("E32", {"action": "delete", "id": uid})
    notify_integrity()
    return "ok", {"message": codes.message_text("M09")}, None, None


def handle_session_list(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды session.list."""
    allowed, err_c, ev_c = _check_caller_permission(payload, "session.list")
    if not allowed:
        return "error", {}, err_c, codes.message_text(err_c)

    s_list = sessions.list_active_sessions()
    return "ok", {"sessions": s_list}, None, None


def handle_session_kill(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """Обработка команды session.kill (FR-35, E05, M15)."""
    allowed, err_c, ev_c = _check_caller_permission(payload, "session.kill")
    if not allowed:
        return "error", {}, err_c, codes.message_text(err_c)

    target_id = payload.get("target_session_id") or payload.get("id", "")
    target_session = sessions.get_session(target_id)
    ok, msg_c, ev_c = sessions.kill_session(target_id)
    if not ok:
        return "error", {}, "M13", codes.message_text("M13")

    if target_session:
        emit_event(ev_c or "E05", {"session_id": target_id, "id": target_session.get("username")})

    return "ok", {"message": codes.message_text("M09")}, None, None


DISPATCH_MAP = {
    "auth.login": handle_auth_login,
    "auth.logout": handle_auth_logout,
    "auth.ping": handle_auth_ping,
    "auth.check": handle_auth_check,
    "user.list": handle_user_list,
    "user.add": handle_user_add,
    "user.edit": handle_user_edit,
    "user.delete": handle_user_delete,
    "session.list": handle_session_list,
    "session.kill": handle_session_kill,
}


def dispatch_request(msg: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str], Optional[str]]:
    """
    Диспетчеризация входящего сообщения:
    handler(msg) -> (status, payload, error_code, error_message).
    """
    cmd = msg.get("cmd")
    payload = msg.get("payload", {})
    handler = DISPATCH_MAP.get(cmd)
    if handler is None:
        return "error", {}, "M14", codes.message_text("M14")
    return handler(payload)


def _init_default_admin() -> None:
    """Инициализация предустановленного администратора admin при первом запуске (FR-33)."""
    user = accounts.get_user(accounts.BUILTIN_ADMIN_ID)
    if user is None:
        # Учётная запись admin по умолчанию: пароль Admin_12345 (фиксируется в ПМИ)
        accounts.add_user(accounts.BUILTIN_ADMIN_ID, "Admin_12345", "rw")


def start_server(socket_path: str = SOCKET_PATH):
    """Запуск сервера Unix-сокета для fw-authd."""
    _init_default_admin()
    emit_event("E12", {"subsystem": "authd"})
    return protocol.serve(socket_path, "authd", dispatch_request)


def main() -> int:
    """Точка входа fw-authd."""
    logger.info("fw-authd: запуск службы авторизации")
    try:
        srv = start_server()
        logger.info("fw-authd: прослушивание сокета %s", SOCKET_PATH)
        srv.serve_forever()
    except (AttributeError, NotImplementedError, OSError) as e:
        logger.warning("fw-authd server cannot be bound: %s", e)
        return 0
    except KeyboardInterrupt:
        logger.info("fw-authd: остановка службы")
        emit_event("E13", {"subsystem": "authd"})
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
