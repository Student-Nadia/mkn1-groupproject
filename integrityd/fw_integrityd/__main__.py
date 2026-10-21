"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-6 Целостность
Модуль:      main
Назначение:  точка входа fw-integrityd: конфигурация, сервер на /run/fw/integrityd.sock, диспетчер команд integrity.*
Методы:
  - load_config — прочитать конфигурацию ПС-6
  - handle — обработать запрос (integrity.check, integrity.status, integrity.restore, integrity.update_baseline)
  - main — запуск подсистемы
"""
import sys

SOCK_PATH = "/run/fw/integrityd.sock"

COMMANDS = ("integrity.check", "integrity.status", "integrity.restore", "integrity.update_baseline")

# Источники команд (таблица «Входящие команды ПС-6»)
ALLOWED_SRC = {
    "integrity.check": ("cli", "web"),
    "integrity.status": ("cli", "web"),
    "integrity.restore": ("cli", "web"),
    "integrity.update_baseline": ("cli", "web", "authd"),
}

CHECK_PERIOD_MIN_SEC = 10
CHECK_PERIOD_MAX_SEC = 3600
MAX_CONTROLLED_FILES = 64


def load_config(path: str = "/etc/fw/config.json") -> dict:
    """Прочитать конфигурацию ПС-6 (baseline_path, backup_dir, hmac_key_path, check_period_sec, files)."""
    raise NotImplementedError("main.load_config")


def handle(msg: dict):
    """Вернуть (status, payload, error_code, error_message) для fwcommon.protocol.serve.
    integrity.update_baseline принимает пустой payload."""
    raise NotImplementedError("main.handle")


def main():
    # TODO: load_config -> проверка при запуске -> периодическая проверка
    #       -> protocol.serve(SOCK_PATH, "integrityd", handle)
    print("fw-integrityd: skeleton, not implemented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
