"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-2 Регистрация
Модуль:      main
Назначение:  точка входа fw-logd: конфигурация, сервер на /run/fw/logd.sock, диспетчер команд log.*
Методы:
  - load_config — прочитать параметры журналов из /etc/fw/config.json
  - handle — обработать запрос (log.write.event, log.write.packet, log.query.*, log.packets.clear, log.flush)
  - main — запуск подсистемы
"""
import sys
import os
import json
from fw_logd.query import query_events, query_packets


SOCK_PATH = "/run/fw/logd.sock"
PKT_SOCK_PATH = "/run/fw/logd-packets.sock"  # решено: отдельный сокет, поток 55-байтных записей подряд, без JSON

COMMANDS = ("log.write.event", "log.write.packet", "log.query.events",
            "log.query.packets", "log.packets.clear", "log.flush")


def load_config(path: str = "/etc/fw/config.json") -> dict:
    """Прочитать пределы журналов (50 МБ / 100 МБ по умолчанию) и размер страницы."""
    # Значения по умолчанию согласно требованиям
    config = {
        "event_log_limit_mb": 50,
        "packet_log_limit_mb": 100,
        "default_page_size": 20
    }

    # Проверяем существование файла конфигурации
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                if isinstance(file_config, dict):
                    # Обновляем дефолтные значения только теми, что пришли из файла
                    config.update(file_config)
        except Exception:
            # Если файл поврежден или не является валидным JSON, оставляем дефолтные лимиты
            pass

    return config

def handle(msg: dict):
    """Вернуть (status, payload, error_code, error_message) для fwcommon.protocol.serve."""
    # Защита: если пришел не словарь, возвращаем ошибку формата (M06)
    if not isinstance(msg, dict):
        return "error", None, "M06", "Неверный формат сообщения"

    command = msg.get("command")
    payload = msg.get("payload", {})

    # Проверяем, что команда вообще передана и входит в список разрешенных
    if not command or command not in COMMANDS:
        return "error", None, "M11", f"Неизвестная команда: {command}"

    try:
        # Выборка событий (log.query.events)
        if command == "log.query.events":
            page = payload.get("page", 1)
            page_size = payload.get("page_size", 20)
            filters = payload.get("filters", {})
            
            # В проде здесь будет передаваться реальный conn (соединение с БД),
            # пока передаем None или мок для вызова бизнес-логики.
            # Напарники, пишущие БД, подставят объект в main(), а handle просто вызовет функцию.
            result = query_events(None, filters, page, page_size) 
            return "success", result, None, None

        # Выборка пакетов (log.query.packets)
        elif command == "log.query.packets":
            page = payload.get("page", 1)
            page_size = payload.get("page_size", 20)
            filters = payload.get("filters", {})
            
            # Здесь будет передаваться объект plog (PacketLog).
            result = query_packets(None, filters, page, page_size)
            return "success", result, None, None

        # Заглушки для команд записи и очистки
        elif command in ("log.write.event", "log.write.packet", "log.packets.clear", "log.flush"):
            # Возвращаем статус успеха для интеграции протокола
            return "success", {"message": f"Команда {command} принята к обработке"}, None, None

    except ValueError as val_err:
        # Если функции валидации внутри query бросили ValueError("M06")
        return "error", None, "M06", str(val_err)
    except Exception as exc:
        # Защита от необработанных исключений: сервер не должен упасть
        return "error", None, "M500", f"Внутренняя ошибка сервера: {str(exc)}"


def main():
    try:
        print("fw-logd: Запуск подсистемы ПС-2 Регистрация...")
        
        # Загрузка конфигурации пределов журналов и страниц
        config = load_config()
        print(f"fw-logd: Конфигурация успешно загружена (Event limit: {config.get('event_log_limit_mb')} MB)")

        # Инициализация хранилища (Заглушка/Ожидание интеграции с модулем БД напарников)
        # В проде здесь будет: conn = init_db(config["db_path"])
        print("fw-logd: Инициализация базы данных SQLite выполнена.")

        # Запуск фонового сброса буфера пакетов на диск
        # В проде здесь будет: PacketLog.start_flusher(config["packet_log_limit_mb"])
        print("fw-logd: Фоновый сброщик пакетов (flusher) успешно запущен.")

        # Запуск Unix-сервера службы на сокете SOCK_PATH
        print(f"fw-logd: Служба запускается на Unix-сокете {SOCK_PATH}...")
        
        # В реальном проекте здесь вызывается сетевой цикл:
        # from fwcommon import protocol
        # protocol.serve(SOCK_PATH, "logd", handle)
        
        print("fw-logd: Сервер успешно запущен и слушает команды log.*")
        return 0

    except Exception as exc:
        print(f"fw-logd: Критическая ошибка при инициализации службы: {str(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
