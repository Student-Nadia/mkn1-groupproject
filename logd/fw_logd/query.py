"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-2 Регистрация
Модуль:      query
Назначение:  выборки по FR-39, постраничный вывод
Методы:
  - events: выборка зарегистрированных событий (п. 3.1, 3.2 ТЗ)
  - packets: выборка обработанных сетевых пакетов (п. 3.3 ТЗ)
"""

import json
import logging
from typing import Dict, Any, Tuple

# Настройка логирования подсистемы ПС-2 Регистрация (fw-logd)
logger = logging.getLogger("fw_logd.query")

# Путь к файлу ошибок
MESSAGES_PATH = "common/messages.json"


def _load_error(error_code: str) -> Dict[str, Any]:
    """
    Внутренний метод: безопасно загружает сообщение об ошибке из common/messages.json.
    Гарантирует возврат структуры (код + сообщение), даже если файл недоступен.
    """
    try:
        with open(MESSAGES_PATH, "r", encoding="utf-8") as f:
            messages = json.load(f)
            message_text = messages.get(error_code, "Неизвестная ошибка системы")
    except Exception as e:
        logger.error(f"Не удалось прочитать {MESSAGES_PATH}: {str(e)}")
        message_text = "Ошибка конфигурации системы сообщений"
        
    return {
        "status": "error",
        "code": error_code,
        "message": message_text
    }


def _validate_input(request_data: Any) -> Tuple[bool, int, int, dict]:
    """
    Внутренний метод: проверяет данные от других подсистем (ПС-3, ПС-4).
    Реализует принцип «не доверять без проверки».
    """
    if not isinstance(request_data, dict):
        return False, 0, 0, {}

    # Извлекаем параметры пагинации по FR-39
    page = request_data.get("page", 1)
    page_size = request_data.get("page_size", 20)
    filters = request_data.get("filters", {})

    try:
        page_num = int(page)
        size_num = int(page_size)
        
        # Защита от некорректных или вредоносных значений
        if page_num < 1 or size_num < 1 or size_num > 100:
            return False, 0, 0, {}
            
        if not isinstance(filters, dict):
            return False, 0, 0, {}
            
        return True, page_num, size_num, filters
    except (ValueError, TypeError):
        return False, 0, 0, {}


def events(request_data: Any) -> Dict[str, Any]:
    """
    Выборка событий (вход/выход администратора, изменение политик и конфигурации).
    п. 3.1, 3.2 ТЗ и постраничный вывод (FR-39).
    """
    try:
        # Валидация входных данных от чужих подсистем
        is_valid, page, page_size, filters = _validate_input(request_data)
        if not is_valid:
            return _load_error("ERR_INVALID_PARAMS")

        # Структура данных по п. 3.1 и 3.2 ТЗ
        # (надо будет написать запрос к БД логов)
        mock_total_events = 3
        items = [
            {
                "datetime": "2026-10-27T10:00:00Z",            # дата и время
                "event_code": "EVT_ADMIN_LOGIN",                # код события
                "description": "Вход администратора в систему",  # описание
                "initiator_id": "admin_main",                   # идентификатор / подсистема
                "admin_ip": "192.168.1.100"                      # IP при удаленном доступе
            },
            {
                "datetime": "2026-10-27T10:05:00Z",
                "event_code": "EVT_FW_START",
                "description": "Включение МЭ и его подсистем",
                "initiator_id": "PS-1_KERNEL",
                "admin_ip": None
            },
            {
                "datetime": "2026-10-27T10:15:00Z",
                "event_code": "EVT_POLICY_CHANGE",
                "description": "Изменение политики доступа",
                "initiator_id": "admin_main",
                "admin_ip": "192.168.1.100"
            }
        ]

        # Расчет страниц для FR-39
        total_pages = (mock_total_events + page_size - 1) // page_size

        return {
            "status": "success",
            "result": {
                "items": items,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_items": mock_total_events,
                    "total_pages": total_pages
                }
            }
        }

    except Exception as exc:
        # необработанные исключения не завершают процесс fw-logd
        logger.critical(f"Критический сбой в log.query.events: {str(exc)}", exc_info=True)
        return _load_error("ERR_INTERNAL_SERVER_ERROR")


def packets(request_data: Any) -> Dict[str, Any]:
    """
    Выборка обработанных сетевых пакетов.
    п. 3.3 ТЗ и постраничный вывод (FR-39).
    """
    try:
        # Валидация входных данных
        is_valid, page, page_size, filters = _validate_input(request_data)
        if not is_valid:
            return _load_error("ERR_INVALID_PARAMS")

        # Полный объем полей регистрации сетевого пакета согласно п. 3.3 ТЗ
        mock_total_packets = 1
        items = [
            {
                "datetime": "2026-10-27T10:14:02Z",        # дата и время
                "action": "DROP",                           # действие над пакетом
                "rule_number": 12,                          # номер правила
                "interface_in": "eth0",                     # входной интерфейс
                "interface_out": "eth1",                    # выходной интерфейс
                "protocol": "TCP",                          # протокол
                "mac_src": "00:0C:29:AB:CD:EF",             # MAC отправителя
                "mac_dst": "00:0C:29:12:34:56",             # MAC получателя
                "ip_src": "192.168.1.50",                   # IP отправителя
                "ip_dst": "10.0.0.1",                       # IP получателя
                "port_src": 49152,                          # порт отправителя (для TCP/UDP)
                "port_dst": 80,                             # порт получателя (для TCP/UDP)
                "icmp_type": None,                          # тип для ICMPv4
                "icmp_code": None                           # код для ICMPv4
            }
        ]

        # Расчет страниц для FR-39
        total_pages = (mock_total_packets + page_size - 1) // page_size

        return {
            "status": "success",
            "result": {
                "items": items,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_items": mock_total_packets,
                    "total_pages": total_pages
                }
            }
        }

    except Exception as exc:
        # необработанные исключения не завершают процесс fw-logd
        logger.critical(f"Критический сбой в log.query.packets: {str(exc)}", exc_info=True)
        return _load_error("ERR_INTERNAL_SERVER_ERROR")
