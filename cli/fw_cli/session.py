"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-3 CLI
Модуль:      session
Назначение:  сеанс администратора: однократный вход через ПС-5 (FR-37a),
             локальный кэш роли, уведомления об активности auth.ping,
             выход; IP-адрес администратора из SSH_CONNECTION (FR-02).
Методы:
  - Session — сеанс: id, роль, источник, IP-адрес
  - client_ip — IP-адрес администратора по переменным SSH (None — консоль)
  - login — auth.login в ПС-5 -> Session (M02, M04, M12)
  - ping — auth.ping: продлить сеанс (M15 — сеанс завершён)
  - logout — auth.logout (E02)
"""
import os
from dataclasses import dataclass


@dataclass
class Session:
    session_id: str
    username: str
    role: str                 # rw | ro — после возможного понижения (FR-34)
    source: str = "cli"       # cli | web
    ip: str = None            # None — локальная консоль
    downgraded: bool = False

    @property
    def is_rw(self):
        return self.role == "rw"


def client_ip(environ=None):
    """IP-адрес администратора: первое поле SSH_CONNECTION или SSH_CLIENT; None — консоль."""
    env = os.environ if environ is None else environ
    for var in ("SSH_CONNECTION", "SSH_CLIENT"):
        parts = env.get(var, "").split()
        if parts:
            return parts[0]
    return None


def login(authd_path, user_id, password, source="cli", ip=None):
    """auth.login -> Session; ProtocolError M02 / M12 / M16. При понижении прав — downgraded."""
    raise NotImplementedError("session.login")


def ping(authd_path, session):
    """auth.ping; ProtocolError M15 — сеанс завершён по таймауту или сброшен."""
    raise NotImplementedError("session.ping")


def logout(authd_path, session):
    """auth.logout; событие E02 регистрирует ПС-5."""
    raise NotImplementedError("session.logout")
